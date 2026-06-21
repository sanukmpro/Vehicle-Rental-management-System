# VRMS Diagrams - A4 Paper Friendly

All diagrams are now in **PlantUML format** and optimized for A4 paper printing.

## Files:

1. `database_er_diagram.puml` - Compact ER Diagram
2. `architecture_diagram.puml` - Simple Architecture Diagram
3. `flow_chart.puml` - Streamlined Flow Chart

## Generate Images (A4 Size):

### Online Method (Recommended):
1. Go to https://www.plantuml.com/plantuml
2. Copy-paste each `.puml` file content
3. Click "Submit" - diagram renders automatically
4. Right-click image → Save as PNG/PDF
5. **For A4 printing**: Use browser print → Scale to fit A4

### VS Code Method:
1. Install "PlantUML" extension
2. Open any `.puml` file
3. Press `Alt+D` or right-click → "Preview current diagram"
4. Export as PNG/PDF

### Command Line (Advanced):
```bash
# Install PlantUML
# For PNG output (A4 friendly):
plantuml -tpng database_er_diagram.puml
plantuml -tpng architecture_diagram.puml
plantuml -tpng flow_chart.puml

# For PDF (direct A4 printing):
plantuml -tpdf database_er_diagram.puml
plantuml -tpdf architecture_diagram.puml
plantuml -tpdf flow_chart.puml
```

## A4 Paper Tips:

- **Compact Design**: All diagrams are minimal and fit A4
- **Font Size**: Optimized for readability on paper
- **White Background**: Print-friendly
- **Simple Layout**: No complex styling that might not print well

## Diagram Features:

- **ER Diagram**: Shows all 7 entities with relationships
- **Architecture**: 5-layer system overview
- **Flow Chart**: Complete user journey in activity diagram format

All diagrams use consistent styling and are designed to be clear when printed on A4 paper.