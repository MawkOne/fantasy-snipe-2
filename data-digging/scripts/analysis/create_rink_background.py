#!/usr/bin/env python3
"""
Create a clean NHL rink background for shot mapping
Based on the zone structure shown in the images
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def create_rink_background():
    """
    Create a clean NHL rink background with zones and markings
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 16))
    
    # Set up the rink dimensions (normalized coordinates)
    # X: 0-100 (center line to goal line)
    # Y: -43 to +43 (sideboard to sideboard)
    
    # Draw the rink outline
    rink_outline = patches.Rectangle((0, -43), 100, 86, 
                                   linewidth=2, edgecolor='black', 
                                   facecolor='lightgray', alpha=0.1)
    ax.add_patch(rink_outline)
    
    # Draw goal line (X=89)
    ax.axvline(x=89, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    
    # Draw blueline (X=75)
    ax.axvline(x=75, color='blue', linewidth=3, alpha=0.8, label='Blueline')
    
    # Draw center line (X=50)
    ax.axvline(x=50, color='blue', linewidth=2, alpha=0.6, linestyle='--', label='Center Line')
    
    # Draw sideboards
    ax.axhline(y=-43, color='black', linewidth=2, alpha=0.5)
    ax.axhline(y=43, color='black', linewidth=2, alpha=0.5)
    
    # Draw center ice line
    ax.axhline(y=0, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    # Draw goal crease (semi-circle in front of goal)
    goal_crease = patches.Arc((89, 0), 12, 8, angle=0, theta1=0, theta2=180, 
                            linewidth=2, color='lightblue', alpha=0.8)
    ax.add_patch(goal_crease)
    
    # Draw face-off circles
    # Left face-off circle
    left_circle = patches.Circle((75, -22), 15, linewidth=2, 
                               edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(left_circle)
    
    # Right face-off circle
    right_circle = patches.Circle((75, 22), 15, linewidth=2, 
                                edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(right_circle)
    
    # Draw face-off dots
    ax.plot(75, -22, 'ro', markersize=3, alpha=0.8)
    ax.plot(75, 22, 'ro', markersize=3, alpha=0.8)
    
    # Draw face-off hash marks
    # Left circle hash marks
    ax.plot([73, 77], [-22, -22], 'r-', linewidth=2, alpha=0.6)
    ax.plot([73, 77], [-20, -20], 'r-', linewidth=2, alpha=0.6)
    ax.plot([73, 77], [-24, -24], 'r-', linewidth=2, alpha=0.6)
    
    # Right circle hash marks
    ax.plot([73, 77], [22, 22], 'r-', linewidth=2, alpha=0.6)
    ax.plot([73, 77], [20, 20], 'r-', linewidth=2, alpha=0.6)
    ax.plot([73, 77], [24, 24], 'r-', linewidth=2, alpha=0.6)
    
    # Create zone boundaries (based on the image structure)
    # High slot area (near goal)
    high_slot = patches.Polygon([(85, -15), (89, -15), (89, 15), (85, 15)], 
                              linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(high_slot)
    
    # Inner slot
    inner_slot = patches.Polygon([(80, -10), (85, -15), (85, 15), (80, 10)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(inner_slot)
    
    # West outer slot
    west_outer = patches.Polygon([(75, -20), (80, -10), (80, -5), (75, -15)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_outer)
    
    # East outer slot
    east_outer = patches.Polygon([(75, 20), (80, 10), (80, 5), (75, 15)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_outer)
    
    # Outside north west (left face-off area)
    outside_nw = patches.Polygon([(75, -43), (85, -43), (85, -20), (75, -20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_nw)
    
    # Outside north east (right face-off area)
    outside_ne = patches.Polygon([(75, 43), (85, 43), (85, 20), (75, 20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_ne)
    
    # West point (left point area)
    west_point = patches.Polygon([(50, -43), (75, -43), (75, -20), (50, -20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_point)
    
    # Center point
    center_point = patches.Polygon([(50, -20), (75, -20), (75, 20), (50, 20)], 
                                 linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(center_point)
    
    # East point (right point area)
    east_point = patches.Polygon([(50, 43), (75, 43), (75, 20), (50, 20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_point)
    
    # Set up the plot
    ax.set_xlim(0, 100)
    ax.set_ylim(-43, 43)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate (Center Line to Goal Line)')
    ax.set_ylabel('Y Coordinate (Sideboard to Sideboard)')
    ax.set_title('NHL Rink Background - Offensive Zone\\nClean version for shot mapping')
    ax.grid(True, alpha=0.3)
    
    # Add zone labels (without percentages)
    ax.text(87, 0, 'Goal Area', ha='center', va='center', fontsize=10, alpha=0.7)
    ax.text(82.5, 0, 'Inner Slot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(77.5, -7.5, 'West Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(77.5, 7.5, 'East Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(80, -31.5, 'Outside\\nNorth West', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(80, 31.5, 'Outside\\nNorth East', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(62.5, -31.5, 'West\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(62.5, 0, 'Center\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(62.5, 31.5, 'East\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    
    # Add coordinate labels
    ax.text(89, -45, 'Goal Line (X=89)', ha='center', va='top', fontsize=8, color='red')
    ax.text(75, -45, 'Blueline (X=75)', ha='center', va='top', fontsize=8, color='blue')
    ax.text(50, -45, 'Center Line (X=50)', ha='center', va='top', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.show()
    
    return fig, ax

def create_simple_rink_background():
    """
    Create a simpler rink background with just the essential markings
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 16))
    
    # Draw the rink outline
    rink_outline = patches.Rectangle((0, -43), 100, 86, 
                                   linewidth=2, edgecolor='black', 
                                   facecolor='lightgray', alpha=0.1)
    ax.add_patch(rink_outline)
    
    # Draw goal line (X=89)
    ax.axvline(x=89, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    
    # Draw blueline (X=75)
    ax.axvline(x=75, color='blue', linewidth=3, alpha=0.8, label='Blueline')
    
    # Draw center line (X=50)
    ax.axvline(x=50, color='blue', linewidth=2, alpha=0.6, linestyle='--', label='Center Line')
    
    # Draw sideboards
    ax.axhline(y=-43, color='black', linewidth=2, alpha=0.5)
    ax.axhline(y=43, color='black', linewidth=2, alpha=0.5)
    
    # Draw center ice line
    ax.axhline(y=0, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    # Draw goal crease (semi-circle in front of goal)
    goal_crease = patches.Arc((89, 0), 12, 8, angle=0, theta1=0, theta2=180, 
                            linewidth=2, color='lightblue', alpha=0.8)
    ax.add_patch(goal_crease)
    
    # Draw face-off circles
    # Left face-off circle
    left_circle = patches.Circle((75, -22), 15, linewidth=2, 
                               edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(left_circle)
    
    # Right face-off circle
    right_circle = patches.Circle((75, 22), 15, linewidth=2, 
                                edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(right_circle)
    
    # Draw face-off dots
    ax.plot(75, -22, 'ro', markersize=3, alpha=0.8)
    ax.plot(75, 22, 'ro', markersize=3, alpha=0.8)
    
    # Set up the plot
    ax.set_xlim(0, 100)
    ax.set_ylim(-43, 43)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate (Center Line to Goal Line)')
    ax.set_ylabel('Y Coordinate (Sideboard to Sideboard)')
    ax.set_title('NHL Rink Background - Simple Version\\nClean version for shot mapping')
    ax.grid(True, alpha=0.3)
    
    # Add coordinate labels
    ax.text(89, -45, 'Goal Line (X=89)', ha='center', va='top', fontsize=8, color='red')
    ax.text(75, -45, 'Blueline (X=75)', ha='center', va='top', fontsize=8, color='blue')
    ax.text(50, -45, 'Center Line (X=50)', ha='center', va='top', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.show()
    
    return fig, ax

def main():
    """
    Main function to create rink backgrounds
    """
    print("Creating NHL Rink Backgrounds for Shot Mapping")
    print("="*50)
    
    print("\\n1. Creating detailed rink background with zones...")
    create_rink_background()
    
    print("\\n2. Creating simple rink background...")
    create_simple_rink_background()
    
    print("\\nRink backgrounds created successfully!")
    print("These can be used as backgrounds for shot mapping visualizations.")

if __name__ == "__main__":
    main()
