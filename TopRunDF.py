# -*- coding: utf-8 -*-
"""
Created on Sun Oct 26 08:05:26 2025
Include sequence of surges
@author: based on cScheidl adapted by NaglG
"""
# -*- coding: utf-8 -*-
import rasterio
import os
import sys
import numpy as np
import json 
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import RandomSingleFlow as randomsfp

#################################################################################################
# Funktion zur Erstellung eines Hillshades basierend auf einem digitalen Höhenmodell
def hillshade(array, azimuth, angle_altitude):
    """Creates a shaded relief file from a DEM."""
    from numpy import gradient, pi, arctan, arctan2, sin, cos, sqrt

    x, y = gradient(array)
    slope = pi / 2.0 - arctan(sqrt(x * x + y * y))
    aspect = arctan2(-x, y)
    azimuthrad = azimuth * pi / 180.0
    altituderad = angle_altitude * pi / 180.0

    shaded = (
        sin(altituderad) * sin(slope)
        + cos(altituderad) * cos(slope) * cos(azimuthrad - aspect)
    )
    return 255 * (shaded + 1) / 2

#################################################################################################
# Funktion zur Adaptierung unterschiedlicher Dezimaltrennzeichen
def parse_decimal(input_string):
    if ',' in input_string and '.' not in input_string:
        input_string = input_string.replace(',', '.')
    try:
        return float(input_string)
    except ValueError:
        raise ValueError("Invalid input. Please enter a number with a valid decimal separator.")

#################################################################################################
def run_simulation(dataset, band1, start_row, start_col, volume, coefficient, gridsize, 
                   artificial_height, artificial_raster_height, workpath):
    """
    Führt eine einzelne Simulation durch und gibt das Ablagerungsraster zurück.
    """
    simarea = volume ** (2 / 3) * coefficient
    mcs = 0
    mcsmax = 500
    perimeter = simarea / gridsize**2
    
    band2 = np.copy(band1)
    band3 = np.copy(band1)
    band3.fill(0)
    area = 0

    # Monte Carlo simulation
    for x in range(0, 100000):
        if area >= perimeter:
            break
        else:
            random_radius = 3
            # Berechne sichere Grenzen für die Zufallsposition
            row_min = max(0, start_row - random_radius)
            row_max = min(dataset.height - 1, start_row + random_radius)
            col_min = max(0, start_col - random_radius)
            col_max = min(dataset.width - 1, start_col + random_radius)
            
            # Stelle sicher, dass row_max > row_min und col_max > col_min
            if row_max <= row_min:
                row = start_row
            else:
                row = np.random.randint(row_min, row_max + 1)
            
            if col_max <= col_min:
                col = start_col
            else:
                col = np.random.randint(col_min, col_max + 1)
            
            position = [row, col]
            band2.fill(0)
            mcs = 0
            
            while (mcs < mcsmax and position[0] <= dataset.height - 1 
                   and position[1] <= dataset.width - 1):
                if position[0] > 0 and position[1] > 0:
                    if area >= perimeter:
                        break
                    else:
                        distance = np.sqrt((position[0] - start_row)**2 + (position[1] - start_col)**2)
                        decay_factor = np.exp(-distance / 100)
                        
                        if isinstance(artificial_height, float):
                            temp_height = artificial_height * gridsize * decay_factor
                        else:
                            temp_height = (
                                artificial_raster_height.read(1)[position[0], position[1]]
                                * gridsize * decay_factor
                            )
                        
                        obj1 = randomsfp.MonteCarloSingleFlowPath(
                        dataset, band2, position, temp_height, current_dem=band1  # <-- NEU: band1 übergeben
                        )
                        position = obj1.NextStartCell()
                        band2[position[0], position[1]] = True
                        band3[position[0], position[1]] += 1
                        if band3[position[0], position[1]] == 1:
                            area += 1
                else:
                    mcs += 1
                    position = [row, col]
                    band2.fill(0)

    band3[0, 0] = 0
    max_val = np.amax(band3)
    if max_val > 0:
        band3 = band3 / max_val
    meanh = volume / perimeter
    band4 = band3 * meanh

    dummy = np.sum(band3)
    if dummy > 0:
        diff = volume / (dummy * gridsize**2)
        meannew = meanh * diff
        band4 = band3 * meannew

    # Diffusionsalgorithmus
    from scipy.ndimage import convolve
    kernel = np.array([[0.05, 0.1, 0.05],
                       [0.1, 0.4, 0.1],
                       [0.05, 0.1, 0.05]])
    band4 = convolve(band4, kernel, mode='constant', cval=0.0)

    # Volumen-Anpassung
    total_deposited_volume = np.sum(band4) * gridsize**2
    volume_difference = volume - total_deposited_volume
    if abs(volume_difference) > 1e-6 and total_deposited_volume > 0:
        adjustment_factor = volume / total_deposited_volume
        band4 *= adjustment_factor
        print(f"  Adjusted deposition values by factor: {adjustment_factor:.4f}")
    
    return band4

#################################################################################################
# Start of the main script
if __name__ == "__main__":
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    fin = None
    
    try:
        # Read the input.json file
        input_file = script_dir / "input.json"
        with open(input_file, "r", encoding="utf-8") as f:
            input_data = json.load(f)
    except BaseException as err:
        fin = "terminated"
        print("Error reading input.json:", err)
    else:
        workpath = script_dir / "DEM"
        
        try:
            # Check if artificial height is specified
            artificial_height = input_data["energy_height"]
            if artificial_height == "elevation":
                artificial_raster_height = rasterio.open(workpath / "elevation.asc")
            else:
                artificial_height = parse_decimal(str(artificial_height))
            
            eventname = input_data["name"]
            
            # Parse volumes - kann entweder einzelner Wert oder Liste sein
            volumes_input = input_data["volume"]
            if isinstance(volumes_input, list):
                volumes = [parse_decimal(str(v)) for v in volumes_input]
            else:
                volumes = [parse_decimal(str(volumes_input))]
            
            print(f"Simuliere {len(volumes)} Volumen: {volumes}")
            
            # Open the DEM file
            dataset = rasterio.open(workpath / "topofan.asc")
            band1_original = dataset.read(1)
            band1 = np.copy(band1_original)  # Aktuelles DEM

            # Generate hillshade vom Original-DEM
            hs_array = hillshade(band1_original, 34, 45)

        except BaseException as err1:
            fin = "terminated"
            print("Error processing DEM or energy height:", err1)
            import traceback
            traceback.print_exc()
        else:
            # Extract simulation parameters
            XKoord = parse_decimal(str(input_data["X_coord"]))
            YKoord = parse_decimal(str(input_data["Y_coord"]))
            coefficient = parse_decimal(str(input_data["coefficient"]))
            gridsize = dataset.res[0]
            start_row, start_col = dataset.index(XKoord, YKoord)
            
            print(f"Startposition: Row={start_row}, Col={start_col}")
            print(f"DEM Dimensionen: {dataset.height} x {dataset.width}")
            print(f"Gridsize: {gridsize} m")

            # Liste zum Speichern der einzelnen Ablagerungen
            deposition_layers = []
            
            # Schleife über alle Volumen
            for i, volume in enumerate(volumes, 1):
                print(f"\n{'='*60}")
                print(f"Simulation {i}/{len(volumes)} - Volumen: {volume} m³")
                print(f"{'='*60}")
                
                # Simulation durchführen
                deposition = run_simulation(
                    dataset, band1, start_row, start_col, volume, coefficient, gridsize,
                    artificial_height, 
                    artificial_raster_height if artificial_height == "elevation" else None,
                    workpath
                )
                
                # Ablagerung speichern
                deposition_layers.append(deposition.copy())
                
                # DEM für nächste Simulation aktualisieren
                band1 = band1 + deposition
                
                # Einzelne Ablagerung speichern
                out_meta = dataset.meta.copy()
                with rasterio.open(workpath / f"depo{i}.asc", "w", **out_meta) as dest:
                    dest.write(deposition, 1)
                print(f"  Gespeichert: depo{i}.asc")
                print(f"  Max. Höhe: {np.max(deposition):.3f} m")
                print(f"  Volumen: {np.sum(deposition) * gridsize**2:.2f} m³")
            
            # Gesamtablagerung berechnen und speichern
            total_deposition = np.sum(deposition_layers, axis=0)
            with rasterio.open(workpath / "depo_total.asc", "w", **out_meta) as dest:
                dest.write(total_deposition, 1)
            
            #############################################################################################
            # VISUALISIERUNG
            #############################################################################################
            
            # Header-Informationen auslesen
            with open(workpath / "depo_total.asc", "r") as prism_f:
                prism_header = prism_f.readlines()[:6]
            
            prism_header = [item.strip().split()[-1] for item in prism_header]
            prism_cols = int(prism_header[0])
            prism_rows = int(prism_header[1])
            prism_xll = float(prism_header[2])
            prism_yll = float(prism_header[3])
            prism_cs = float(prism_header[4])
            
            prism_extent = [
                prism_xll,
                prism_xll + prism_cols * prism_cs,
                prism_yll,
                prism_yll + prism_rows * prism_cs,
            ]
            
            # Farbpaletten für verschiedene Ablagerungen definieren
            color_maps = ['Reds', 'Blues', 'Greens', 'Purples', 'Oranges', 'YlOrBr']
            
            # Plot 1: Einzelne Ablagerungen übereinander
            fig, ax = plt.subplots(figsize=(12, 10))
            ax.set_title(f"Multi-Event Deposition - {eventname}", fontsize=14, fontweight='bold')
            
            # Hillshade als Hintergrund
            ax.imshow(hs_array, extent=prism_extent, cmap="Greys", alpha=0.5)
            
            # Jede Ablagerung mit eigener Farbe
            for i, depo_layer in enumerate(deposition_layers):
                masked_depo = np.ma.masked_where(depo_layer < 0.005, depo_layer)
                cmap = plt.cm.get_cmap(color_maps[i % len(color_maps)])
                im = ax.imshow(masked_depo, extent=prism_extent, alpha=0.6, cmap=cmap)
                
                # Einzelne Colorbar für jede Ablagerung
                cbar = plt.colorbar(im, ax=ax, orientation="vertical", 
                                   pad=0.02 + i*0.08, aspect=14, shrink=0.8)
                cbar.set_label(f"Event {i+1} ({volumes[i]:.0f} m³) [m]", fontsize=10)
            
            ax.set_xlabel("X [m]")
            ax.set_ylabel("Y [m]")
            plt.tight_layout()
            plt.savefig(workpath / "deposition_multi_event.png", dpi=300, bbox_inches='tight')
            
            # Plot 2: Gesamtablagerung
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            ax2.set_title(f"Total Deposition - {eventname}\nTotal: {sum(volumes):.0f} m³", 
                         fontsize=14, fontweight='bold')
            
            # Hillshade als Hintergrund
            ax2.imshow(hs_array, extent=prism_extent, cmap="Greys", alpha=0.5)
            
            # Gesamtablagerung
            masked_total = np.ma.masked_where(total_deposition < 0.005, total_deposition)
            cmap_total = plt.cm.OrRd
            cmap_total.set_bad(color="white")
            im2 = ax2.imshow(masked_total, extent=prism_extent, cmap=cmap_total)
            
            cbar2 = plt.colorbar(im2, ax=ax2, orientation="vertical", aspect=14)
            cbar2.set_label("Total deposition heights [m]", fontsize=11)
            
            ax2.set_xlabel("X [m]")
            ax2.set_ylabel("Y [m]")
            plt.tight_layout()
            plt.savefig(workpath / "deposition_total.png", dpi=300, bbox_inches='tight')
            
            # Plot 3: Vergleichsdarstellung (Subplots)
            n_events = len(volumes)
            fig3, axes = plt.subplots(1, n_events + 1, figsize=(5*(n_events+1), 4))
            if n_events == 1:
                axes = [axes[0], axes[1]]  # Sicherstellen dass axes immer eine Liste ist
            fig3.suptitle(f"Event Comparison - {eventname}", fontsize=16, fontweight='bold')
            
            # Einzelne Events
            for i, (ax, depo_layer) in enumerate(zip(axes[:-1], deposition_layers)):
                ax.imshow(hs_array, extent=prism_extent, cmap="Greys", alpha=0.5)
                masked_depo = np.ma.masked_where(depo_layer < 0.005, depo_layer)
                cmap = plt.cm.get_cmap(color_maps[i % len(color_maps)])
                im = ax.imshow(masked_depo, extent=prism_extent, cmap=cmap)
                ax.set_title(f"Event {i+1}\n{volumes[i]:.0f} m³")
                plt.colorbar(im, ax=ax, orientation="vertical", aspect=10, pad=0.02)
                ax.set_xlabel("X [m]")
                if i == 0:
                    ax.set_ylabel("Y [m]")
            
            # Gesamtablagerung
            axes[-1].imshow(hs_array, extent=prism_extent, cmap="Greys", alpha=0.5)
            masked_total = np.ma.masked_where(total_deposition < 0.005, total_deposition)
            im_total = axes[-1].imshow(masked_total, extent=prism_extent, cmap='OrRd')
            axes[-1].set_title(f"Total\n{sum(volumes):.0f} m³")
            plt.colorbar(im_total, ax=axes[-1], orientation="vertical", aspect=10, pad=0.02)
            axes[-1].set_xlabel("X [m]")
            
            plt.tight_layout()
            plt.savefig(workpath / "deposition_comparison.png", dpi=300, bbox_inches='tight')
            
            fin = "finished"
            
            # Statistik ausgeben
            print(f"\n{'='*60}")
            print("SIMULATION ABGESCHLOSSEN")
            print(f"{'='*60}")
            print(f"Anzahl Events: {len(volumes)}")
            print(f"Einzelne Volumen: {volumes}")
            print(f"Gesamtvolumen: {sum(volumes):.2f} m³")
            print(f"Max. Ablagerungshöhe: {np.max(total_deposition):.3f} m")
            if np.sum(total_deposition > 0) > 0:
                print(f"Mittlere Ablagerungshöhe: {np.mean(total_deposition[total_deposition > 0]):.3f} m")
            print(f"\nGespeicherte Dateien:")
            print(f"  - depo1.asc bis depo{len(volumes)}.asc (Einzelne Events)")
            print(f"  - depo_total.asc (Gesamtablagerung)")
            print(f"  - deposition_multi_event.png (Überlagerung)")
            print(f"  - deposition_total.png (Gesamtansicht)")
            print(f"  - deposition_comparison.png (Vergleich)")
            print(f"{'='*60}\n")
            
            plt.show()
            
    finally:
        if fin is None:
            fin = "terminated"
        print("Simulation", fin)