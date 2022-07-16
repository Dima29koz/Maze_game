function drawMapInteractive(data) {
    const canvas = data.canvas;
    const context = data.canvas.getContext('2d');
    const TILE_SIZE = data.tile_size;
    const rows = data.rows;
    const cols = data.cols;



    class Player {
        constructor(x, y) {
            this.x = x;
            this.y = y;
            this.area = new Path2D();
            let x_px = this.x * TILE_SIZE;
            let y_px = this.y * TILE_SIZE;
            this.area.arc(x_px + TILE_SIZE / 2, y_px + TILE_SIZE / 2, TILE_SIZE * 0.3, 0, 2 * Math.PI);
        }

        draw(context) {
            context.fillStyle = 'black';
            context.fill(this.area);
        }

        data() {
            return { 'x': this.x, 'y': this.y };
        }
    }

    class Cell {
        constructor(x, y, type='empty') {
            this.x = x;
            this.y = y;
            this.type = type;
            this.players = [];
            this.area = new Path2D();
            let x_px = this.x * TILE_SIZE;
            let y_px = this.y * TILE_SIZE;
            this.area.rect(x_px + TILE_SIZE * 0.2, y_px + TILE_SIZE * 0.2, TILE_SIZE * 0.8, TILE_SIZE * 0.8);
        }

        draw(context) {
            switch (this.type) {
                case 'ground':
                    context.fillStyle = '#967C21'
                    break;
                case 'river':
                    context.fillStyle = '#0B5394'
                    break;
                default:
                    context.fillStyle = '#CCCCCC'
                    break;
            }
            context.fill(this.area);
            for (player of this.players) {
                player.draw(context);
            }
        }

        data() {
            return { 'x': this.x, 'y': this.y };
        }

        setType(type) {
            this.type = type;
        }

        addPlayer(player) {
            if (this.players.length > 0) {
                this.players = [];
            } else {
                this.players.push(player);
            }

        }
    }

    class Wall {
        constructor(x, y, dir, type='empty') {
            this.x = x;
            this.y = y;
            this.dir = dir;
            this.type = type;
            this.area = new Path2D();
            this.create_area();
        }

        create_area() {
            let x_px = this.x * TILE_SIZE;
            let y_px = this.y * TILE_SIZE;
            switch (this.dir) {
                case 'top':
                    this.area.rect(x_px + TILE_SIZE * 0.2, y_px, TILE_SIZE * 0.8, TILE_SIZE * 0.2);
                    break;
                case 'bottom':
                    this.area.rect(x_px + TILE_SIZE * 0.2, y_px + TILE_SIZE, TILE_SIZE * 0.8, TILE_SIZE * 0.2);
                    break;
                case 'left':
                    this.area.rect(x_px, y_px + TILE_SIZE * 0.2, TILE_SIZE * 0.2, TILE_SIZE * 0.8);
                    break;
                case 'right':
                    this.area.rect(x_px + TILE_SIZE, y_px + TILE_SIZE * 0.2, TILE_SIZE * 0.2, TILE_SIZE * 0.8);
                    break;
                default:
                    console.log('error. wall creation');
                    break;
            }

        }

        data() {
            return { 'x': this.x, 'y': this.y, 'dir': this.dir };
        }

        draw(context) {
            switch (this.type) {
                case 'outer':
                    context.fillStyle = '#660000'
                    break;
                case 'concrete':
                    context.fillStyle = '#663300'
                    break;
                default:
                    context.fillStyle = '#999999'
                    break;
            }
            context.fill(this.area);
        }

        setType(type) {
            this.type = type;
        }
    }

    class Palette {
        constructor(context, cols) {

            this.cells = [new Cell(cols+1, 0, 'ground'), new Cell(cols+1, 1, 'river')];
            this.walls = [new Wall(cols+2, 0, 'right', 'outer'), new Wall(cols+2, 1, 'right', 'concrete')];

            this.context = context;
            this.cell_mode = 'ground';
            this.wall_mode = 'empty';
        }

        draw () {
            for (let cell of this.cells) {
                cell.draw(this.context);
            }
            for (let wall of this.walls) {
                wall.draw(this.context);
            }
        }

        setCellMode(mode) {
            this.cell_mode = mode;
            console.log(mode);
        }
        setWallMode(mode) {
            this.wall_mode = mode;
            console.log(mode);
        }
    }

    class Grid {
        constructor(rows, cols, context) {
            this.context = context;
            this.rows = rows;
            this.cols = cols;
            this.cells = this.create_cells();
            this.walls = this.create_walls();
            this.palette = new Palette(context, cols);
        }

        create_cells() {
            let cells = [];
            for (let y=0; y<this.rows; y++) {
                for (let x=0; x<this.cols; x++) {
                    cells.push(new Cell(x, y));
                }
            }
            return cells;
        }

        create_walls() {
            let walls = [];
            for (let x=0; x<this.cols; x++) {
                walls.push(new Wall(x, 0, 'top'));
            }
            for (let y=0; y<this.rows; y++) {
                walls.push(new Wall(0, y, 'left'));
            }
            for (let cell of this.cells) {
                walls.push(new Wall(cell.x, cell.y, 'bottom'));
                walls.push(new Wall(cell.x, cell.y, 'right'));
            }
            return walls;
        }

        draw() {
            for (let cell of this.cells) {
                cell.draw(this.context);
            }
            for (let wall of this.walls) {
                wall.draw(this.context);
            }
            this.palette.draw();
        }

        onObjUpdate(obj, type) {
            obj.setType(type);
            obj.draw(this.context);

        }
    }

    let grid = new Grid(rows, cols, context);
    grid.draw(context);

    let template_cells = grid.palette.cells;
    let template_walls = grid.palette.walls;

    canvas.addEventListener('click', procLClick, false);
    canvas.addEventListener('mouseout', procOut, false);
    canvas.addEventListener('contextmenu', procRClick, false);

    function procLClick(e) {
        grid.cells.forEach(cell => {
            if(context.isPointInPath(cell.area, e.offsetX, e.offsetY)){
                grid.onObjUpdate(cell, grid.palette.cell_mode);
            }
        })
        grid.walls.forEach(wall => {
            if(context.isPointInPath(wall.area, e.offsetX, e.offsetY)){
                grid.onObjUpdate(wall, grid.palette.wall_mode);
            }
        })
        template_cells.forEach(t => {
            if(context.isPointInPath(t.area, e.offsetX, e.offsetY)){
                grid.palette.setCellMode(t.type);
            }
        })
        template_walls.forEach(t => {
            if(context.isPointInPath(t.area, e.offsetX, e.offsetY)){
                grid.palette.setWallMode(t.type);
            }
        })
    }

    function procRClick(e) {
        e.preventDefault();
        grid.cells.forEach(f => {
            if (context.isPointInPath(f.area, e.offsetX, e.offsetY)) {
                let player = new Player(f.x, f.y);
                f.addPlayer(player);
                grid.draw();
            }
        })
    }

    function procOut() {
        document.body.style.cursor = "default";
    }

}



