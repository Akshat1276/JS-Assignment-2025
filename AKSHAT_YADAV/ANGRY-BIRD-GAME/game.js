// --- Blocks state ---
let blocks = [
  { x: 600, y: 400, w: 60, h: 40 },
  { x: 700, y: 400, w: 60, h: 40 },
  { x: 650, y: 350, w: 60, h: 40 },
  { x: 800, y: 420, w: 80, h: 40 },
  { x: 900, y: 420, w: 80, h: 40 }
];
const BLOCK_COLOR = '#8d6e63';
const BLOCK_BORDER = '#4e342e';
// Boilerplate for Angry Bird Game
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

let projectile = null; // { pos: Vector, vel: Vector }
const GRAVITY = 0.35; // Tune this value for gravity strength
let trail = []; // Array of Vector positions for the projectile's path
const TRAIL_MAX = 100; // Max number of trail points
const GROUND_HEIGHT_FRAC = 0.2; // 20% of canvas height
let groundY = 0; // Will be set in resizeCanvas
const BALL_RADIUS = 15;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  groundY = canvas.height - Math.floor(canvas.height * GROUND_HEIGHT_FRAC);
  // Always place ball at fixed position on ground if not in flight
  if (!projectile || (!projectile.vel.x && !projectile.vel.y)) {
    projectile = {
      pos: new Vector(120, groundY - BALL_RADIUS),
      vel: new Vector(0, 0),
      r: BALL_RADIUS
    };
    trail = [];
  }
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// --- Vector class ---
class Vector {
  constructor(x = 0, y = 0) {
    this.x = x;
    this.y = y;
  }
  clone() {
    return new Vector(this.x, this.y);
  }
  add(v) {
    this.x += v.x;
    this.y += v.y;
    return this;
  }
  sub(v) {
    this.x -= v.x;
    this.y -= v.y;
    return this;
  }
  scale(s) {
    this.x *= s;
    this.y *= s;
    return this;
  }
  length() {
    return Math.sqrt(this.x * this.x + this.y * this.y);
  }
  normalize() {
    const len = this.length();
    if (len > 0) {
      this.x /= len;
      this.y /= len;
    }
    return this;
  }
  static fromPoints(a, b) {
    return new Vector(b.x - a.x, b.y - a.y);
  }
}

// --- Input handling for drag ---
let isDragging = false;
let dragStart = null;
let dragEnd = null;

canvas.addEventListener('pointerdown', (e) => {
  const dx = e.offsetX - projectile.pos.x;
  const dy = e.offsetY - projectile.pos.y;
  if (Math.sqrt(dx*dx + dy*dy) <= BALL_RADIUS + 10 && !projectile.vel.x && !projectile.vel.y) {
    isDragging = true;
    dragStart = projectile.pos.clone();
    dragEnd = dragStart.clone();
  }
});
canvas.addEventListener('pointermove', (e) => {
  if (isDragging) {
    dragEnd = new Vector(e.offsetX, e.offsetY);
  }
});
canvas.addEventListener('pointerup', (e) => {
  if (isDragging) {
    dragEnd = new Vector(e.offsetX, e.offsetY);
    // Launch projectile
    const launchVec = Vector.fromPoints(dragEnd, dragStart); // From end to start (slingshot)
    const power = Math.min(launchVec.length(), 150); // Limit max power
    const velocity = launchVec.clone().normalize().scale(power * 0.25); // Tune 0.05 for speed
    projectile = {
      pos: dragStart.clone(),
      vel: velocity,
      r: BALL_RADIUS
    };
    trail = [dragStart.clone()]; // Start trail at launch point
    isDragging = false;
  }
});
canvas.addEventListener('pointerleave', (e) => {
  isDragging = false;
});

function clear() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function circleVsAABB(circle, rect) {
  // Find closest point to circle within the rectangle
  let closestX = Math.max(rect.x, Math.min(circle.x, rect.x + rect.w));
  let closestY = Math.max(rect.y, Math.min(circle.y, rect.y + rect.h));
  // Calculate distance from circle center to closest point
  let dx = circle.x - closestX;
  let dy = circle.y - closestY;
  return (dx * dx + dy * dy) <= (circle.r * circle.r);
}

function update() {
  if (projectile) {
    if (projectile.vel.x || projectile.vel.y) {
      projectile.vel.y += GRAVITY;
      projectile.pos.add(projectile.vel);
      trail.push(projectile.pos.clone());
      if (trail.length > TRAIL_MAX) trail.shift();
      if (
        projectile.pos.x < 0 || projectile.pos.x > canvas.width ||
        projectile.pos.y > canvas.height || projectile.pos.y > groundY - BALL_RADIUS + 2
      ) {
        projectile = {
          pos: new Vector(120, groundY - BALL_RADIUS),
          vel: new Vector(0, 0),
          r: BALL_RADIUS
        };
        trail = [];
      }
    }
  }
}

function render() {
  // Draw blocks
  for (const block of blocks) {
    ctx.save();
    ctx.fillStyle = BLOCK_COLOR;
    ctx.strokeStyle = BLOCK_BORDER;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.rect(block.x, block.y, block.w, block.h);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }
  // Draw projectile trail as dotted line
  if (trail.length > 1) {
    ctx.save();
    ctx.strokeStyle = '#888';
    ctx.setLineDash([4, 8]);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(trail[0].x, trail[0].y);
    for (let i = 1; i < trail.length; i++) {
      ctx.lineTo(trail[i].x, trail[i].y);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  }
  // Draw projectile
  if (projectile) {
    ctx.save();
    ctx.fillStyle = '#ffeb3b';
    ctx.beginPath();
    ctx.arc(projectile.pos.x, projectile.pos.y, projectile.r, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#fbc02d';
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.restore();
  }
  // Draw drag line if dragging
  if (dragStart && dragEnd && (isDragging || (!isDragging && dragStart !== dragEnd))) {
    ctx.save();
    ctx.strokeStyle = '#d32f2f';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(dragStart.x, dragStart.y);
    ctx.lineTo(dragEnd.x, dragEnd.y);
    ctx.stroke();
    ctx.restore();
    // Draw drag start point
    ctx.save();
    ctx.fillStyle = '#1976d2';
    ctx.beginPath();
    ctx.arc(dragStart.x, dragStart.y, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
  // Draw ground
  ctx.save();
  ctx.fillStyle = '#388e3c';
  ctx.fillRect(0, groundY, canvas.width, canvas.height - groundY);
  ctx.restore();
}

function gameLoop() {
  clear();
  update();
  render();
  requestAnimationFrame(gameLoop);
}
gameLoop();
