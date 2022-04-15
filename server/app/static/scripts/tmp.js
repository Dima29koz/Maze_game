const TILE_SIZE = 50;

let example = document.getElementById("example");
let ctx = example.getContext('2d');
example.width  = 640;
example.height = 480;

class Player {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.area = new Path2D();
        let x_px = this.x * TILE_SIZE;
        let y_px = this.y * TILE_SIZE;
        this.area.arc(x_px + TILE_SIZE * 1.5, y_px + TILE_SIZE * 1.5, TILE_SIZE * 0.3, 0, 2 * Math.PI);
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
        this.state = 'empty';
        this.players = [];
        this.area = new Path2D();
        let x_px = this.x * TILE_SIZE;
        let y_px = this.y * TILE_SIZE;
        this.area.rect(x_px + TILE_SIZE, y_px + TILE_SIZE, TILE_SIZE * 0.8, TILE_SIZE * 0.8);
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

    setState(type) {
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
    constructor(x, y, dir) {
        this.x = x;
        this.y = y;
        this.dir = dir;
        this.state = 'empty';
        this.area = new Path2D();
        this.create_area();
    }

    create_area() {
        let x_px = this.x * TILE_SIZE;
        let y_px = this.y * TILE_SIZE;
        switch (this.dir) {
            case 'top':
                this.area.rect(x_px + TILE_SIZE, y_px + TILE_SIZE * 0.8, TILE_SIZE * 0.8, TILE_SIZE * 0.2);
                break;
            case 'bottom':
                this.area.rect(x_px + TILE_SIZE, y_px + TILE_SIZE * 1.8, TILE_SIZE * 0.8, TILE_SIZE * 0.2);
                break;
            case 'left':
                this.area.rect(x_px + TILE_SIZE * 0.8, y_px + TILE_SIZE, TILE_SIZE * 0.2, TILE_SIZE * 0.8);
                break;
            case 'right':
                this.area.rect(x_px + TILE_SIZE * 1.8, y_px + TILE_SIZE, TILE_SIZE * 0.2, TILE_SIZE * 0.8);
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
        context.fillStyle = this.state == 'empty'? 'blue' : 'green';
        context.fill(this.area);
    }

    setState(state) {
        this.state = state;
    }
}

class Palette {
    constructor(context, cols) {

        this.cells = [new Cell(cols+1, 0, 'ground'), new Cell(cols+1, 1, 'river')];
        this.wall = true;

        this.context = context;
        this.mode = 'ground';
    }

    draw () {
        for (let cell of this.cells) {
            cell.draw(this.context);
        }
    }

    setMode(mode) {
        this.mode = mode;
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
        obj.setState(type);
        obj.draw(this.context);

    }
}

let grid = new Grid(4, 5, ctx);
grid.draw(ctx);

let figures = grid.walls.concat(grid.cells);
let templates = grid.palette.cells;

example.addEventListener('click', procLClick, false);
//example.addEventListener('mousemove', procMove, false);
example.addEventListener('mouseout', procOut, false);
example.addEventListener('contextmenu', procRClick, false);

function procLClick(e) {
    figures.forEach(f => {
        if(ctx.isPointInPath(f.area, e.offsetX, e.offsetY)){
            grid.onObjUpdate(f, grid.palette.mode);
        }
    })
    templates.forEach(t => {
        if(ctx.isPointInPath(t.area, e.offsetX, e.offsetY)){
            grid.palette.setMode(t.type);
        }
  })
};

function procMove(e) {
    figures.forEach(f => {
        if (ctx.isPointInPath(f.area, e.offsetX, e.offsetY)) {
            grid.onObjUpdate(f, 'hovered');
        } else {
            grid.onObjUpdate(f, 'empty');
        }
    })

};

function procRClick(e) {
    e.preventDefault();
    figures.forEach(f => {
        if (ctx.isPointInPath(f.area, e.offsetX, e.offsetY)) {
            console.log(f.data(), 'rclick');
            player = new Player(f.x, f.y);
            f.addPlayer(player);
            grid.draw();
        }
    })
};
function procOut() {
    document.body.style.cursor = "default";
};