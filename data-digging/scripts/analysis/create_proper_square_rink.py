#!/usr/bin/env python3
"""
Create NHL rink background with proper square appearance
Adjusting coordinate system to make it more square-like
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def create_proper_square_rink():
    """
    Create rink background that appears square
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # Adjust the coordinate system to make it more square
    # Instead of 75-89 (14 units) by -43 to +43 (86 units)
    # Let's use a more square coordinate system
    
    # Draw the rink outline - make it more square
    rink_outline = patches.Rectangle((0, -40), 40, 80, 
                                   linewidth=2, edgecolor='black', 
                                   facecolor='lightgray', alpha=0.1)
    ax.add_patch(rink_outline)
    
    # Draw goal line (X=40) - at the right
    ax.axvline(x=40, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    
    # Draw blueline (X=0) - at the left
    ax.axvline(x=0, color='blue', linewidth=3, alpha=0.8, label='Blueline')
    
    # Draw sideboards
    ax.axhline(y=-40, color='black', linewidth=2, alpha=0.5)
    ax.axhline(y=40, color='black', linewidth=2, alpha=0.5)
    
    # Draw center ice line
    ax.axhline(y=0, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    # Draw goal crease (semi-circle in front of goal)
    goal_crease = patches.Arc((40, 0), 8, 6, angle=0, theta1=0, theta2=180, 
                            linewidth=2, color='lightblue', alpha=0.8)
    ax.add_patch(goal_crease)
    
    # Draw face-off circles
    # Left face-off circle
    left_circle = patches.Circle((0, -20), 12, linewidth=2, 
                               edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(left_circle)
    
    # Right face-off circle
    right_circle = patches.Circle((0, 20), 12, linewidth=2, 
                                edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(right_circle)
    
    # Draw face-off dots
    ax.plot(0, -20, 'ro', markersize=3, alpha=0.8)
    ax.plot(0, 20, 'ro', markersize=3, alpha=0.8)
    
    # Create zone boundaries
    # Goal Area (behind net area)
    goal_area = patches.Polygon([(40, -6), (40, 6), (38, 6), (38, -6)], 
                              linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(goal_area)
    
    # Inner Slot (high danger area)
    inner_slot = patches.Polygon([(35, -10), (40, -6), (40, 6), (35, 10)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(inner_slot)
    
    # West Outer Slot
    west_outer = patches.Polygon([(30, -15), (35, -10), (35, -5), (30, -10)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_outer)
    
    # East Outer Slot
    east_outer = patches.Polygon([(30, 15), (35, 10), (35, 5), (30, 10)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_outer)
    
    # Outside North West (left face-off area)
    outside_nw = patches.Polygon([(0, -40), (35, -40), (35, -15), (30, -15), (0, -20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_nw)
    
    # Outside North East (right face-off area)
    outside_ne = patches.Polygon([(0, 40), (35, 40), (35, 15), (30, 15), (0, 20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_ne)
    
    # West Point (left point area)
    west_point = patches.Polygon([(0, -40), (30, -40), (30, -15), (0, -20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_point)
    
    # Center Point
    center_point = patches.Polygon([(0, -15), (30, -15), (30, 15), (0, 15)], 
                                 linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(center_point)
    
    # East Point (right point area)
    east_point = patches.Polygon([(0, 40), (30, 40), (30, 15), (0, 20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_point)
    
    # Set up the plot with proper square aspect ratio
    ax.set_xlim(-5, 45)
    ax.set_ylim(-45, 45)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate (Blueline to Goal Line) - Horizontal')
    ax.set_ylabel('Y Coordinate (Sideboard to Sideboard) - Vertical')
    ax.set_title('NHL Offensive Zone - Square Layout\\nX Horizontal, Y Vertical')
    ax.grid(True, alpha=0.3)
    
    # Add zone labels
    ax.text(39, 0, 'Goal Area', ha='center', va='center', fontsize=10, alpha=0.7)
    ax.text(37.5, 0, 'Inner Slot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(32.5, -7.5, 'West Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(32.5, 7.5, 'East Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(17.5, -27.5, 'Outside\\nNorth West', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(17.5, 27.5, 'Outside\\nNorth East', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(15, -27.5, 'West\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(15, 0, 'Center\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(15, 27.5, 'East\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    
    # Add coordinate labels
    ax.text(40, -42, 'Goal Line (X=40)', ha='center', va='top', fontsize=8, color='red')
    ax.text(0, -42, 'Blueline (X=0)', ha='center', va='top', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.show()
    
    return fig, ax

def create_simple_square_rink():
    """
    Create a simple square rink background
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # Draw the rink outline - make it square
    rink_outline = patches.Rectangle((0, -40), 40, 80, 
                                   linewidth=2, edgecolor='black', 
                                   facecolor='lightgray', alpha=0.1)
    ax.add_patch(rink_outline)
    
    # Draw goal line (X=40) - at the right
    ax.axvline(x=40, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    
    # Draw blueline (X=0) - at the left
    ax.axvline(x=0, color='blue', linewidth=3, alpha=0.8, label='Blueline')
    
    # Draw sideboards
    ax.axhline(y=-40, color='black', linewidth=2, alpha=0.5)
    ax.axhline(y=40, color='black', linewidth=2, alpha=0.5)
    
    # Draw center ice line
    ax.axhline(y=0, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    # Draw goal crease (semi-circle in front of goal)
    goal_crease = patches.Arc((40, 0), 8, 6, angle=0, theta1=0, theta2=180, 
                            linewidth=2, color='lightblue', alpha=0.8)
    ax.add_patch(goal_crease)
    
    # Draw face-off circles
    # Left face-off circle
    left_circle = patches.Circle((0, -20), 12, linewidth=2, 
                               edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(left_circle)
    
    # Right face-off circle
    right_circle = patches.Circle((0, 20), 12, linewidth=2, 
                                edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(right_circle)
    
    # Draw face-off dots
    ax.plot(0, -20, 'ro', markersize=3, alpha=0.8)
    ax.plot(0, 20, 'ro', markersize=3, alpha=0.8)
    
    # Set up the plot with proper square aspect ratio
    ax.set_xlim(-5, 45)
    ax.set_ylim(-45, 45)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate (Blueline to Goal Line) - Horizontal')
    ax.set_ylabel('Y Coordinate (Sideboard to Sideboard) - Vertical')
    ax.set_title('NHL Offensive Zone - Simple Square Version\\nX Horizontal, Y Vertical')
    ax.grid(True, alpha=0.3)
    
    # Add coordinate labels
    ax.text(40, -42, 'Goal Line (X=40)', ha='center', va='top', fontsize=8, color='red')
    ax.text(0, -42, 'Blueline (X=0)', ha='center', va='top', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.show()
    
    return fig, ax

def main():
    """
    Main function to create proper square rink backgrounds
    """
    print("Creating NHL Rink Backgrounds - Proper Square Layout")
    print("Adjusted coordinate system for square appearance")
    print("="*60)
    
    print("\\n1. Creating detailed offensive zone with zones...")
    create_proper_square_rink()
    
    print("\\n2. Creating simple offensive zone...")
    create_simple_square_rink()
    
    print("\\nProper square rink backgrounds created successfully!")
    print("Now with adjusted coordinate system for square appearance.")

if __name__ == "__main__":
    main()
