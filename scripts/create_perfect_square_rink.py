#!/usr/bin/env python3
"""
Create perfect square NHL rink background
Goal at top, proper face-off circle positioning, 100x100 coordinate system
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def create_perfect_square_rink():
    """
    Create perfect square rink background with goal at top
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # Perfect square coordinate system: 0-100 by 0-100
    # Goal at top (Y=100), blueline at bottom (Y=0)
    # X: 0-100 (left to right sideboard)
    # Y: 0-100 (blueline to goal line)
    
    # Draw the rink outline - perfect square
    rink_outline = patches.Rectangle((0, 0), 100, 100, 
                                   linewidth=2, edgecolor='black', 
                                   facecolor='lightgray', alpha=0.1)
    ax.add_patch(rink_outline)
    
    # Draw goal line (Y=100) - at the top
    ax.axhline(y=100, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    
    # Draw blueline (Y=0) - at the bottom
    ax.axhline(y=0, color='blue', linewidth=3, alpha=0.8, label='Blueline')
    
    # Draw sideboards
    ax.axvline(x=0, color='black', linewidth=2, alpha=0.5)
    ax.axvline(x=100, color='black', linewidth=2, alpha=0.5)
    
    # Draw center ice line
    ax.axvline(x=50, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    # Draw goal crease (semi-circle in front of goal)
    goal_crease = patches.Arc((50, 100), 12, 8, angle=0, theta1=0, theta2=180, 
                            linewidth=2, color='lightblue', alpha=0.8)
    ax.add_patch(goal_crease)
    
    # Draw face-off circles
    # Left face-off circle (25 units from left side, at blueline)
    left_circle = patches.Circle((25, 0), 15, linewidth=2, 
                               edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(left_circle)
    
    # Right face-off circle (25 units from right side, at blueline)
    right_circle = patches.Circle((75, 0), 15, linewidth=2, 
                                edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(right_circle)
    
    # Draw face-off dots (1 unit radius at circle centers)
    ax.plot(25, 0, 'ro', markersize=6, alpha=0.8)
    ax.plot(75, 0, 'ro', markersize=6, alpha=0.8)
    
    # Create zone boundaries following the exact layout from images
    # Goal Area (behind net area)
    goal_area = patches.Polygon([(40, 100), (60, 100), (60, 95), (40, 95)], 
                              linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(goal_area)
    
    # Inner Slot (high danger area)
    inner_slot = patches.Polygon([(35, 85), (40, 100), (60, 100), (65, 85)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(inner_slot)
    
    # West Outer Slot
    west_outer = patches.Polygon([(20, 70), (35, 85), (40, 85), (25, 70)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_outer)
    
    # East Outer Slot
    east_outer = patches.Polygon([(80, 70), (65, 85), (60, 85), (75, 70)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_outer)
    
    # Outside North West (left face-off area)
    outside_nw = patches.Polygon([(0, 0), (0, 20), (20, 20), (25, 70), (0, 70)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_nw)
    
    # Outside North East (right face-off area)
    outside_ne = patches.Polygon([(100, 0), (100, 20), (80, 20), (75, 70), (100, 70)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(outside_ne)
    
    # West Point (left point area)
    west_point = patches.Polygon([(0, 0), (0, 70), (25, 70), (20, 20), (0, 20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(west_point)
    
    # Center Point
    center_point = patches.Polygon([(20, 0), (80, 0), (75, 70), (25, 70)], 
                                 linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(center_point)
    
    # East Point (right point area)
    east_point = patches.Polygon([(100, 0), (100, 70), (75, 70), (80, 20), (100, 20)], 
                               linewidth=1, edgecolor='gray', facecolor='none', alpha=0.3)
    ax.add_patch(east_point)
    
    # Set up the plot with perfect square aspect ratio
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate (Left to Right) - Horizontal')
    ax.set_ylabel('Y Coordinate (Blueline to Goal Line) - Vertical')
    ax.set_title('NHL Offensive Zone - Perfect Square\\nGoal at Top, 100x100 Coordinate System')
    ax.grid(True, alpha=0.3)
    
    # Add zone labels
    ax.text(50, 97.5, 'Goal Area', ha='center', va='center', fontsize=10, alpha=0.7)
    ax.text(50, 92.5, 'Inner Slot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(30, 77.5, 'West Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(70, 77.5, 'East Outer\\nSlot', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(12.5, 35, 'Outside\\nNorth West', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(87.5, 35, 'Outside\\nNorth East', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(12.5, 10, 'West\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(50, 10, 'Center\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    ax.text(87.5, 10, 'East\\nPoint', ha='center', va='center', fontsize=9, alpha=0.7)
    
    # Add coordinate labels
    ax.text(-2, 100, 'Goal Line (Y=100)', ha='right', va='center', fontsize=8, color='red')
    ax.text(-2, 0, 'Blueline (Y=0)', ha='right', va='center', fontsize=8, color='blue')
    ax.text(50, -2, 'Center Line (X=50)', ha='center', va='top', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.show()
    
    return fig, ax

def create_simple_perfect_square_rink():
    """
    Create simple perfect square rink background
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # Perfect square coordinate system: 0-100 by 0-100
    # Goal at top (Y=100), blueline at bottom (Y=0)
    
    # Draw the rink outline - perfect square
    rink_outline = patches.Rectangle((0, 0), 100, 100, 
                                   linewidth=2, edgecolor='black', 
                                   facecolor='lightgray', alpha=0.1)
    ax.add_patch(rink_outline)
    
    # Draw goal line (Y=100) - at the top
    ax.axhline(y=100, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    
    # Draw blueline (Y=0) - at the bottom
    ax.axhline(y=0, color='blue', linewidth=3, alpha=0.8, label='Blueline')
    
    # Draw sideboards
    ax.axvline(x=0, color='black', linewidth=2, alpha=0.5)
    ax.axvline(x=100, color='black', linewidth=2, alpha=0.5)
    
    # Draw center ice line
    ax.axvline(x=50, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    # Draw goal crease (semi-circle in front of goal)
    goal_crease = patches.Arc((50, 100), 12, 8, angle=0, theta1=0, theta2=180, 
                            linewidth=2, color='lightblue', alpha=0.8)
    ax.add_patch(goal_crease)
    
    # Draw face-off circles
    # Left face-off circle (25 units from left side, at blueline)
    left_circle = patches.Circle((25, 0), 15, linewidth=2, 
                               edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(left_circle)
    
    # Right face-off circle (25 units from right side, at blueline)
    right_circle = patches.Circle((75, 0), 15, linewidth=2, 
                                edgecolor='red', facecolor='none', alpha=0.6)
    ax.add_patch(right_circle)
    
    # Draw face-off dots (1 unit radius at circle centers)
    ax.plot(25, 0, 'ro', markersize=6, alpha=0.8)
    ax.plot(75, 0, 'ro', markersize=6, alpha=0.8)
    
    # Set up the plot with perfect square aspect ratio
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate (Left to Right) - Horizontal')
    ax.set_ylabel('Y Coordinate (Blueline to Goal Line) - Vertical')
    ax.set_title('NHL Offensive Zone - Simple Perfect Square\\nGoal at Top, 100x100 Coordinate System')
    ax.grid(True, alpha=0.3)
    
    # Add coordinate labels
    ax.text(-2, 100, 'Goal Line (Y=100)', ha='right', va='center', fontsize=8, color='red')
    ax.text(-2, 0, 'Blueline (Y=0)', ha='right', va='center', fontsize=8, color='blue')
    ax.text(50, -2, 'Center Line (X=50)', ha='center', va='top', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.show()
    
    return fig, ax

def main():
    """
    Main function to create perfect square rink backgrounds
    """
    print("Creating Perfect Square NHL Rink Backgrounds")
    print("Goal at top, 100x100 coordinate system, proper face-off positioning")
    print("="*70)
    
    print("\\n1. Creating detailed perfect square offensive zone...")
    create_perfect_square_rink()
    
    print("\\n2. Creating simple perfect square offensive zone...")
    create_simple_perfect_square_rink()
    
    print("\\nPerfect square rink backgrounds created successfully!")
    print("Goal at top, perfect 1:1 aspect ratio, proper face-off circles and dots.")

if __name__ == "__main__":
    main()
