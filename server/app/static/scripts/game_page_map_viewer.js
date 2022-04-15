function drawMap(field, treasures, players, current_user) {
    const drawingCanvas = document.getElementById('map-debug');
    const div = document.getElementById('map-debug-container');
    width = div.clientWidth;
    height = div.clientHeight;
    tile_size = height < width ? height / field.length : width / field[0].length;
    if(drawingCanvas && drawingCanvas.getContext) {
        let context = drawingCanvas.getContext('2d');
        context.canvas.width  = width;
        context.canvas.height = tile_size * field.length;
        let cells = drawField(context);
        drawTreasures(context);
        drawPlayers(context);

        drawingCanvas.onclick = e => {
            cells.forEach(cell_obj => {
                if(context.isPointInPath(cell_obj, e.offsetX, e.offsetY)){
                    console.log(cell_obj.data);
                }
            })
        }
    }

    function drawField(context) {
        let cells = [];
        for (row of field) {
            for (cell of row) {
                if (cell.type) {
                    cells.push(drawCell(cell, context));
                    drawWalls(cell.walls, context);
                }
            }
        }
        return cells;

        function drawCell(cell, context) {
            let cell_obj = new Path2D();
            x = cell.x * tile_size;
            y = cell.y * tile_size;
            cell_obj.rect(x+2, y+2, tile_size-4, tile_size-4);
            cell_obj.data = { 'x': cell.x, 'y': cell.y };
            context.fillStyle = getCellColor(cell.type);
            context.fill(cell_obj);
            if (cell.type == 'CellRiver' || cell.type == 'CellRiverMouth') {
                drawRiverDir(cell, x, y, context);
            }
            if (cell.type == 'CellClinic') {
                drawClinic(cell, x, y, context);
            }
            if (cell.type == 'CellArmory' || cell.type == 'CellArmoryWeapon') {
                drawArmory(cell, x, y, context);
            }
            if (cell.type == 'CellArmoryExplosive') {
                drawArmoryExplosive(cell, x, y, context);
            }
            return cell_obj;
        }

        function getCellColor(type_str) {
            switch (type_str) {
                case 'CellExit':
                    return '#377814';
                case 'CellRiver':
                case 'CellRiverMouth':
                    return '#0044cc';

                default:
                    return '#6b623c';
            }
        }

        function drawWalls(walls, context) {
            x = cell.x * tile_size;
            y = cell.y * tile_size;

            context.fillStyle = getWallColor(walls.top);
            context.fillRect(x, y, tile_size, 4);

            context.fillStyle = getWallColor(walls.right);
            context.fillRect(x+tile_size-4, y, 4, tile_size);

            context.fillStyle = getWallColor(walls.left);
            context.fillRect(x, y, 4, tile_size);

            context.fillStyle = getWallColor(walls.bottom);
            context.fillRect(x, y+tile_size-4, tile_size, 4);
        }

        function getWallColor(type_str) {
            switch (type_str) {
                case 'WallOuter':
                    return '#3c2d0f';
                case 'WallConcrete':
                    return '#aa6919'
                case 'WallExit':
                    return '#37ac19';
                case 'WallRubber':
                    return '#0f0f0f';
                default:
                    return '#2F4F4F';
            }
        }

        function drawRiverDir(cell, x, y, context) {
            context.font = `${tile_size  / 2}px serif`;
            context.fillStyle = 'white'
            let direction = '';
            switch (cell.river_dir) {
                case 'top':
                    direction = '↑';
                    break;
                case 'bottom':
                    direction = '↓';
                    break;
                case 'right':
                    direction = '→';
                    break;
                case 'left':
                    direction = '←';
                    break;
                default:
                    direction = 'o';
                    break;
            }
            context.fillText(direction, x + tile_size / 2, y + tile_size / 2);
        }

        function drawClinic(cell, x, y, context) {
            context.font = `${tile_size  / 2}px serif`;
            context.fillStyle = 'red';
            context.fillText('H', x + tile_size / 2, y + tile_size / 2);
        }

        function drawArmory(cell, x, y, context) {
            context.font = `${tile_size  / 2}px serif`;
            context.fillStyle = 'red';

            context.fillText('W', x + tile_size / 2, y + tile_size / 2);
        }

        function drawArmoryExplosive(cell, x, y, context) {
            context.font = `${tile_size  / 2}px serif`;
            context.fillStyle = 'red';
            context.fillText('E', x + tile_size / 2, y + tile_size / 2);
        }
    }

    function drawTreasures(context) {
        for (treasure of treasures) {
            x = treasure.x * tile_size;
            y = treasure.y * tile_size;
            drawTreasure(x, y, treasure.type, context);
        }
    }

    function drawTreasure(x, y, type_str, context) {
        let color = '';
        switch (type_str) {
            case 'spurious':
                color = '#41cf25';
                break;
            case 'mined':
                color = '#cf3c25';
                break;
            default:
                color = '#cfb225';
                break;
        }
        context.fillStyle = color;
        context.fillRect(x + tile_size / 3 + 2, y + tile_size / 3 + 2, tile_size / 3 -2 , tile_size / 3 - 2);
    }

    function drawPlayers(context) {
        for (player of players) {
            x = player.x * tile_size + tile_size / 2;
            y = player.y * tile_size + tile_size / 2;
            context.beginPath();
            context.arc(x,y, tile_size / 3.5 ,0,Math.PI*2,true);
            context.fillStyle = 'red';
            context.fill();
            if (player.name == current_user) {
                context.lineWidth = 3;
                context.strokeStyle = 'white';
                context.stroke();
            }
        }
    }
}