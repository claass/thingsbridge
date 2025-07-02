#!/usr/bin/env python3
"""
ThingsBridge Architecture Diagram Generator
Creates a visual representation of the codebase structure.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Define colors for different layers
colors = {
    'entry': '#E8F4FD',      # Light blue
    'tools': '#D4EDDA',      # Light green  
    'script': '#FFF3CD',     # Light yellow
    'core': '#F8D7DA',       # Light red
    'cache': '#E2E3E5',      # Light gray
    'test': '#D1ECF1',       # Light cyan
    'util': '#F5F5F5'        # Very light gray
}

# Define box style
box_style = "round,pad=0.1"

def create_box(ax, x, y, width, height, text, color, text_size=9):
    """Create a rounded rectangle box with text."""
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle=box_style,
        facecolor=color,
        edgecolor='black',
        linewidth=1
    )
    ax.add_patch(box)
    
    # Add text
    ax.text(x + width/2, y + height/2, text, 
            ha='center', va='center', fontsize=text_size, 
            weight='bold', wrap=True)

def create_arrow(ax, start_x, start_y, end_x, end_y, color='black', style='-'):
    """Create an arrow between two points."""
    arrow = ConnectionPatch(
        (start_x, start_y), (end_x, end_y), 
        "data", "data",
        arrowstyle="->", 
        shrinkA=5, shrinkB=5,
        color=color,
        linewidth=1.5,
        linestyle=style
    )
    ax.add_patch(arrow)

# Title
ax.text(5, 9.5, 'ThingsBridge Architecture Overview', 
        ha='center', va='center', fontsize=18, weight='bold')

# Layer 1: Entry Point
create_box(ax, 4, 8.5, 2, 0.6, 'server.py\n(MCP Entry Point)', colors['entry'])

# Layer 2: Tool Facade
create_box(ax, 4, 7.5, 2, 0.6, 'tools.py\n(Import Facade)', colors['tools'])

# Layer 3: Tool Modules
create_box(ax, 1, 6.2, 1.8, 0.8, 'core_tools.py\n(CRUD Operations)\n540 lines', colors['tools'])
create_box(ax, 3.2, 6.2, 1.8, 0.8, 'search_tools.py\n(Search & Lists)\n335 lines', colors['tools'])
create_box(ax, 5.4, 6.2, 1.8, 0.8, 'bulk_tools.py\n(Batch Ops)\n750 lines', colors['tools'])
create_box(ax, 7.6, 6.2, 1.8, 0.8, 'resources.py\n(MCP Resources)\n230 lines', colors['tools'])

# Layer 4: AppleScript Generation
create_box(ax, 2, 4.8, 2.2, 0.8, 'applescript_builder.py\n(Script Generation)\n716 lines', colors['script'])
create_box(ax, 5.8, 4.8, 2.2, 0.8, 'things3.py\n(Client)\n108 lines', colors['script'])

# Layer 5: Core Systems
create_box(ax, 1, 3.4, 1.8, 0.8, 'applescript.py\n(Executor)\n93 lines', colors['core'])
create_box(ax, 3.2, 3.4, 1.8, 0.8, 'cache.py\n(Multi-level Cache)\n236 lines', colors['cache'])
create_box(ax, 5.4, 3.4, 1.8, 0.8, 'utils.py\n(Shared Utils)\n186 lines', colors['util'])

# Layer 6: Testing Infrastructure  
create_box(ax, 7.6, 3.4, 1.8, 0.8, 'tests/\n(11 test files)\nCleanup System', colors['test'])

# Add arrows showing main dependencies
# Entry to facade
create_arrow(ax, 5, 8.5, 5, 8.1)

# Facade to tools
create_arrow(ax, 4.5, 7.5, 2, 7.0)
create_arrow(ax, 5, 7.5, 4.1, 7.0)
create_arrow(ax, 5.5, 7.5, 6.3, 7.0)
create_arrow(ax, 5.5, 7.5, 8.5, 7.0)

# Tools to AppleScript
create_arrow(ax, 2, 6.2, 3, 5.6)
create_arrow(ax, 4, 6.2, 3.5, 5.6)
create_arrow(ax, 6.3, 6.2, 5, 5.6)

# AppleScript builder to executor
create_arrow(ax, 3, 4.8, 2, 4.2)

# Things3 client to AppleScript
create_arrow(ax, 6.5, 4.8, 2.5, 4.2)

# Cache connections (dashed)
create_arrow(ax, 4.1, 3.4, 2.5, 4.8, style='--', color='gray')
create_arrow(ax, 4.1, 3.4, 6.5, 4.8, style='--', color='gray')

# Utils connections (dotted)
create_arrow(ax, 6.3, 3.4, 3.5, 4.8, style=':', color='gray')

# Add legend
legend_y = 2.5
ax.text(0.5, legend_y + 0.8, 'Legend:', fontsize=12, weight='bold')

legend_items = [
    ('Entry Points', colors['entry']),
    ('Tool Layer', colors['tools']),
    ('AppleScript', colors['script']),
    ('Core Systems', colors['core']),
    ('Caching', colors['cache']),
    ('Testing', colors['test']),
    ('Utilities', colors['util'])
]

for i, (label, color) in enumerate(legend_items):
    y_pos = legend_y + 0.5 - i * 0.2
    create_box(ax, 0.5, y_pos - 0.05, 0.3, 0.1, '', color, text_size=8)
    ax.text(0.9, y_pos, label, fontsize=10, va='center')

# Add performance notes
ax.text(5, 2.2, 'Key Performance Features:', fontsize=12, weight='bold', ha='center')
ax.text(5, 1.8, '• Bulk operations: 5-10x faster than individual calls', fontsize=10, ha='center')
ax.text(5, 1.5, '• Resource caching: 37,000x - 54,000x speed improvement', fontsize=10, ha='center')
ax.text(5, 1.2, '• Native batch AppleScript execution (~40ms for 500 items)', fontsize=10, ha='center')
ax.text(5, 0.9, '• Automatic test artifact cleanup system', fontsize=10, ha='center')

# Add data flow indicators
ax.text(8.5, 8.8, 'Data Flow:', fontsize=10, weight='bold')
ax.text(8.5, 8.5, '1. MCP Request', fontsize=9)
ax.text(8.5, 8.3, '2. Tool Dispatch', fontsize=9)
ax.text(8.5, 8.1, '3. Script Generation', fontsize=9)
ax.text(8.5, 7.9, '4. AppleScript Execution', fontsize=9)
ax.text(8.5, 7.7, '5. Things 3 Integration', fontsize=9)
ax.text(8.5, 7.5, '6. Response & Caching', fontsize=9)

plt.tight_layout()
plt.savefig('/Users/ldc/Desktop/hearthware/thingsbridge/thingsbridge_architecture.png', 
            dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
plt.show()

print("Architecture diagram saved as 'thingsbridge_architecture.png'")