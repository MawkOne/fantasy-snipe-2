#!/usr/bin/env python3
"""
Create NHL rink background with proper square aspect ratio
X horizontal, Y vertical, but with correct proportions
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def create_square_rink_background():
    """
    Create rink background with proper square aspect ratio
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    
    # Set up the rink dimensions (normalized coordinates)
    # X: 75-89 (blueline to goal line) - only offensive zone
    # Y: -43 to +43 (sideboard to sideboard)
    
    # Draw the rink outline (only offensive zone)
    rink_outline = patches.Rectangle((75, -43), 14, 86, 
                                   linewidth=2, edgecolor='black', 
                                   facecolor='lightgray', alpha=0.1)
    ax.add_patch(rink_outline)
    
    # Draw goal line (X=89) - at the right
    ax.axvline(x=89, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    
    # Draw blueline (X=75) - at the left
    ax.axvline(x=75, color='blue', linewidth=3, alpha=0.8, label='Blueline')
    
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
    
    # Create zone boundaries following the exact layout from images
    # Goal Area (behind net area)
    goal_area = patches.Polygon([(89, -8), (89, 8), (87, 8), (87, -8)], 
                              linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(goal_area)
    
    # Inner Slot (high danger area)
    inner_slot = patches.Polygon([(85, -12), (89, -8), (89, 8), (85, 12)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(inner_slot)
    
    # West Outer Slot
    west_outer = patches.Polygon([(80, -18), (85, -12), (85, -8), (80, -14)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_outer)
    
    # East Outer Slot
    east_outer = patches.Polygon([(80, 18), (85, 12), (85, 8), (80, 14)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_outer)
    
    # Outside North West (left face-off area)
    outside_nw = patches.Polygon([(75, -43), (85, -43), (85, -18), (80, -18), (75, -22)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_nw)
    
    # Outside North East (right face-off area)
    outside_ne = patches.Polygon([(75, 43), (85, 43), (85, 18), (80, 18), (75, 22)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_ne)
    
    # West Point (left point area)
    west_point = patches.Polygon([(75, -43), (80, -43), (80, -18), (75, -22)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_point)
    
    # Center Point
    center_point = patches.Polygon([(75, -18), (80, -18), (80, 18), (75, 18)], 
                                 linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(center_point)
    
    # East Point (right point area)
    east_point = patches.Polygon([(75, 43), (80, 43), (80, 18), (75, 22)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_point)
    
    # Set up the plot with proper square aspect ratio
    ax.set_xlim(75, 89)
    ax.set_ylim(-43, 43)
    ax.set_aspect('equal')  # This makes it square
    ax.set_xlabel('X Coordinate (Blueline to Goal Line) - Horizontal')
    ax.set_ylabel('Y Coordinate (Sideboard to Sideboard) - Vertical')
    ax.set_title('NHL Offensive Zone - Square Aspect Ratio\\nX Horizontal, Y Vertical')
    ax.grid(True, alpha=0.3)
    
    # Add zone labels (without percentages)
    ax.text(88, 0, 'Goal Area', ha='center', va='center', fontsize=10, alpha=0.7)
    ax.text(87, 0, 'Inner Slot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(82.5, -10, 'West Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(82.5, 10, 'East Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(80, -30, 'Outside\\nNorth West', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(80, 30, 'Outside\\nNorth East', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(77.5, -30, 'West\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(77.5, 0, 'Center\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(77.5, 30, 'East\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    
    # Add coordinate labels
    ax.text(89, -45, 'Goal Line (X=89)', ha='center', va='top', fontsize=8, color='red')
    ax.text(75, -45, 'Blueline (X=75)', ha='center', va='top', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.show()
    
    return fig, ax

def create_simple_square_offensive_zone():
    """
    Create a simple offensive zone background with square aspect ratio
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    
    # Draw the rink outline (only offensive zone)
    rink_outline = patches.Rectangle((75, -43), 14, 86, 
                                   linewidth=2, edgecolor='black', 
                                   facecolor='lightgray', alpha=0.1)
    ax.add_patch(rink_outline)
    
    # Draw goal line (X=89) - at the right
    ax.axvline(x=89, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    
    # Draw blueline (X=75) - at the left
    ax.axvline(x=75, color='blue', linewidth=3, alpha=0.8, label='Blueline')
    
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
    
    # Set up the plot with proper square aspect ratio
    ax.set_xlim(75, 89)
    ax.set_ylim(-43, 43)
    ax.set_aspect('equal')  # This makes it square
    ax.set_xlabel('X Coordinate (Blueline to Goal Line) - Horizontal')
    ax.set_ylabel('Y Coordinate (Sideboard to Sideboard) - Vertical')
    ax.set_title('NHL Offensive Zone - Simple Square Version\\nX Horizontal, Y Vertical')
    ax.grid(True, alpha=0.3)
    
    # Add coordinate labels
    ax.text(89, -45, 'Goal Line (X=89)', ha='center', va='top', fontsize=8, color='red')
    ax.text(75, -45, 'Blueline (X=75)', ha='center', va='top', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.show()
    
    return fig, ax

def main():
    """
    Main function to create square rink backgrounds
    """
    print("Creating NHL Rink Backgrounds - Square Aspect Ratio")
    print("X Horizontal, Y Vertical, Proper Proportions")
    print("="*60)
    
    print("\\n1. Creating detailed offensive zone with zones...")
    create_square_rink_background()
    
    print("\\n2. Creating simple offensive zone...")
    create_simple_square_offensive_zone()
    
    print("\\nSquare rink backgrounds created successfully!")
    print("Now with proper square aspect ratio and proportions.")

if __name__ == "__main__":
    main()
