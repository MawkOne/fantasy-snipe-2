#!/usr/bin/env python3
"""
Create NHL rink background with proper square appearance
Using a different approach to make it truly square
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def create_final_square_rink():
    """
    Create rink background that appears square
    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    
    # Use a square coordinate system: 0-100 by 0-100
    # This will make it naturally square
    
    # Draw the rink outline - make it square
    rink_outline = patches.Rectangle((0, 0), 100, 100, 
                                   linewidth=2, edgecolor='black', 
                                   facecolor='lightgray', alpha=0.1)
    ax.add_patch(rink_outline)
    
    # Draw goal line (X=100) - at the right
    ax.axvline(x=100, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    
    # Draw blueline (X=0) - at the left
    ax.axvline(x=0, color='blue', linewidth=3, alpha=0.8, label='Blueline')
    
    # Draw sideboards
    ax.axhline(y=0, color='black', linewidth=2, alpha=0.5)
    ax.axhline(y=100, color='black', linewidth=2, alpha=0.5)
    
    # Draw center ice line
    ax.axhline(y=50, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    # Draw goal crease (semi-circle in front of goal)
    goal_crease = patches.Arc((100, 50), 20, 15, angle=0, theta1=0, theta2=180, 
                            linewidth=2, color='lightblue', alpha=0.8)
    ax.add_patch(goal_crease)
    
    # Draw face-off circles
    # Left face-off circle
    left_circle = patches.Circle((0, 25), 15, linewidth=2, 
                               edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(left_circle)
    
    # Right face-off circle
    right_circle = patches.Circle((0, 75), 15, linewidth=2, 
                                edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(right_circle)
    
    # Draw face-off dots
    ax.plot(0, 25, 'ro', markersize=3, alpha=0.8)
    ax.plot(0, 75, 'ro', markersize=3, alpha=0.8)
    
    # Create zone boundaries
    # Goal Area (behind net area)
    goal_area = patches.Polygon([(100, 40), (100, 60), (95, 60), (95, 40)], 
                              linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(goal_area)
    
    # Inner Slot (high danger area)
    inner_slot = patches.Polygon([(85, 35), (100, 40), (100, 60), (85, 65)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(inner_slot)
    
    # West Outer Slot
    west_outer = patches.Polygon([(70, 20), (85, 35), (85, 40), (70, 25)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_outer)
    
    # East Outer Slot
    east_outer = patches.Polygon([(70, 80), (85, 65), (85, 60), (70, 75)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_outer)
    
    # Outside North West (left face-off area)
    outside_nw = patches.Polygon([(0, 0), (85, 0), (85, 20), (70, 20), (0, 25)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_nw)
    
    # Outside North East (right face-off area)
    outside_ne = patches.Polygon([(0, 100), (85, 100), (85, 80), (70, 80), (0, 75)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_ne)
    
    # West Point (left point area)
    west_point = patches.Polygon([(0, 0), (70, 0), (70, 20), (0, 25)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_point)
    
    # Center Point
    center_point = patches.Polygon([(0, 20), (70, 20), (70, 80), (0, 80)], 
                                 linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(center_point)
    
    # East Point (right point area)
    east_point = patches.Polygon([(0, 100), (70, 100), (70, 80), (0, 75)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_point)
    
    # Set up the plot with proper square aspect ratio
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate (Blueline to Goal Line) - Horizontal')
    ax.set_ylabel('Y Coordinate (Sideboard to Sideboard) - Vertical')
    ax.set_title('NHL Offensive Zone - Square Layout\\nX Horizontal, Y Vertical')
    ax.grid(True, alpha=0.3)
    
    # Add zone labels
    ax.text(97.5, 50, 'Goal Area', ha='center', va='center', fontsize=10, alpha=0.7)
    ax.text(92.5, 50, 'Inner Slot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(77.5, 30, 'West Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(77.5, 70, 'East Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(42.5, 10, 'Outside\\nNorth West', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(42.5, 90, 'Outside\\nNorth East', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(35, 10, 'West\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(35, 50, 'Center\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(35, 90, 'East\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    
    # Add coordinate labels
    ax.text(100, -2, 'Goal Line (X=100)', ha='center', va='top', fontsize=8, color='red')
    ax.text(0, -2, 'Blueline (X=0)', ha='center', va='top', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.show()
    
    return fig, ax

def main():
    """
    Main function to create final square rink background
    """
    print("Creating Final NHL Rink Background - Square Layout")
    print("Using 0-100 coordinate system for perfect square")
    print("="*60)
    
    print("\\nCreating square offensive zone...")
    create_final_square_rink()
    
    print("\\nFinal square rink background created successfully!")
    print("Now with 0-100 coordinate system for perfect square appearance.")

if __name__ == "__main__":
    main()
