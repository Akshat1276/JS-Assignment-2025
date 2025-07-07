console.log("Script start");
window.addEventListener("DOMContentLoaded", () => {
  try {
    //level selector dropdown
    const select = document.createElement("select");
    select.id = "levelSelect";
    select.style.position = "absolute";
    select.style.top = "10px";
    select.style.left = "10px";
    ["Level 1", "Level 2", "Level 3"].forEach((name, i) => {
      const opt = document.createElement("option");
      opt.value = i;
      opt.text = name;
      select.appendChild(opt);
    });
    document.body.appendChild(select);

    const canvas = document.getElementById("gameCanvas");
    if (!canvas) throw new Error("#gameCanvas not found");
    const ctx = canvas.getContext("2d");

    // Physics
    const GRAVITY = 0.35,
      BOUNCE = -0.6;
    const groundFrac = 0.2,
      BALL_RADIUS = 15;
    const LOCKOUT_MS = 4500,
      MAX_SHOTS = 3,
      TRAIL_MAX = 100;

    // Level definitions
    const levels = [
      {
        // Level 1
        walls: [
          { x: 400, y: 300, w: 20, h: 200 },
          { x: 600, y: 350, w: 20, h: 150 },
          { x: 450, y: 380, w: 150, h: 20, isFloor: true },
        ],
        target: { x: 700, y: 330, w: 40, h: 40 },
      },
      {
        // Level 2
        walls: [
          // Central tall pillar
          { x: 580, y: 240, w: 40, h: 200 },
          // Left descending ramp
          { x: 450, y: 380, w: 50, h: 20, isFloor: true },
          { x: 500, y: 400, w: 50, h: 20 },
          { x: 550, y: 420, w: 50, h: 20 },
          // Right ascending ramp
          { x: 700, y: 420, w: 50, h: 20, isFloor: true },
          { x: 650, y: 400, w: 50, h: 20 },
          { x: 600, y: 380, w: 50, h: 20 },
          // Overhead rotating beam
          { x: 550, y: 300, w: 200, h: 20, isFloor: true },
          { x: 550, y: 260, w: 20, h: 40 },
          { x: 730, y: 220, w: 20, h: 100 },
        ],
        target: { x: 640, y: 280, w: 20, h: 20 },
      },
      {
        // Level 3
        walls: [
          { x: 500, y: 420, w: 300, h: 20, isFloor: true },
          { x: 520, y: 400, w: 40, h: 20 },
          { x: 560, y: 380, w: 40, h: 20 },
          { x: 600, y: 360, w: 40, h: 20 },
          { x: 640, y: 340, w: 40, h: 20 },
          { x: 680, y: 320, w: 40, h: 20 },
          { x: 780, y: 280, w: 20, h: 160 },
        ],
        target: { x: 720, y: 380, w: 30, h: 30 },
      },
    ];

    // State
    let groundY, slingStart;
    let projectile = null;
    let lastShotTime = 0,
      allowShoot = true;
    let shotsTaken = 0,
      gameOver = false,
      targetHit = false;
    let currentLevel = 0;

    // Collision
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
      length() {
        return Math.hypot(this.x, this.y);
      }
      normalize() {
        let l = this.length();
        if (l > 0) {
          this.x /= l;
          this.y /= l;
        }
        return this;
      }
      scale(s) {
        this.x *= s;
        this.y *= s;
        return this;
      }
      static fromPoints(a, b) {
        return new Vector(b.x - a.x, b.y - a.y);
      }
    }
    const circleVsAABB = (c, r) => {
      const cx = Math.max(r.x, Math.min(c.x, r.x + r.w)),
        cy = Math.max(r.y, Math.min(c.y, r.y + r.h)),
        dx = c.x - cx,
        dy = c.y - cy;
      return dx * dx + dy * dy <= c.r * c.r;
    };

    function resizeCanvas() {
      canvas.width = innerWidth;
      canvas.height = innerHeight;
      groundY = canvas.height * (1 - groundFrac);
      slingStart = new Vector(150, groundY - BALL_RADIUS);
    }
    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    // Level switch
    select.addEventListener("change", () => {
      currentLevel = +select.value;
      resetLevel();
    });
    function resetLevel() {
      projectile = null;
      shotsTaken = 0;
      gameOver = false;
      targetHit = false;
      allowShoot = true;
    }
    resetLevel();

    // Input
    let isDragging = false,
      dragEnd = null;
    canvas.addEventListener("pointerdown", (e) => {
      if (!allowShoot || shotsTaken >= MAX_SHOTS || gameOver) return;
      isDragging = true;
      dragEnd = new Vector(e.offsetX, e.offsetY);
    });
    canvas.addEventListener("pointermove", (e) => {
      if (isDragging) dragEnd = new Vector(e.offsetX, e.offsetY);
    });
    canvas.addEventListener("pointerup", (e) => {
      if (!isDragging || !allowShoot) return;
      isDragging = false;
      const launch = Vector.fromPoints(dragEnd, slingStart);
      const power = Math.min(launch.length(), 150);
      const vel = launch
        .clone()
        .normalize()
        .scale(power * 0.25);
      projectile = {
        pos: slingStart.clone(),
        vel,
        trail: [slingStart.clone()],
      };
      lastShotTime = performance.now();
      allowShoot = false;
      shotsTaken++;
    });
    function update() {
      const now = performance.now();
      if (
        !projectile ||
        projectile.vel.length() < 0.1 ||
        now - lastShotTime > LOCKOUT_MS
      )
        allowShoot = true;
      const lvl = levels[currentLevel];
      if (projectile && !targetHit) {
        projectile.vel.y += GRAVITY;
        projectile.pos.add(projectile.vel);
        if (projectile.pos.y + BALL_RADIUS > groundY) {
          projectile.pos.y = groundY - BALL_RADIUS;
          projectile.vel.y *= BOUNCE;
          projectile.vel.x *= Math.abs(BOUNCE);
        }
        lvl.walls.forEach((w) => {
          if (
            circleVsAABB(
              { x: projectile.pos.x, y: projectile.pos.y, r: BALL_RADIUS },
              w
            )
          ) {
            if (w.isFloor) {
              projectile.pos.y = w.y - BALL_RADIUS;
              projectile.vel.y *= BOUNCE;
              projectile.vel.x *= Math.abs(BOUNCE);
            } else {
              projectile.vel.x *= -1;
              projectile.vel.y *= BOUNCE;
              if (projectile.pos.x < w.x) projectile.pos.x = w.x - BALL_RADIUS;
              else projectile.pos.x = w.x + w.w + BALL_RADIUS;
            }
          }
        });
        const tgt = lvl.target;
        if (
          circleVsAABB(
            { x: projectile.pos.x, y: projectile.pos.y, r: BALL_RADIUS },
            tgt
          )
        ) {
          targetHit = true;
          gameOver = true;
        }
        projectile.trail.push(projectile.pos.clone());
        // if (projectile.trail.length > TRAIL_MAX) projectile.trail.shift();
        if (
          projectile.pos.x < 0 ||
          projectile.pos.x > canvas.width ||
          projectile.pos.y > canvas.height
        )
          projectile = null;
      }
    }

    function render() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#795548";
      ctx.fillRect(0, groundY, canvas.width, canvas.height - groundY);
      const lvl = levels[currentLevel];
      ctx.fillStyle = "#8d6e63";
      lvl.walls.forEach((w) => ctx.fillRect(w.x, w.y, w.w, w.h));
      const tgt = lvl.target;
      ctx.fillStyle = targetHit ? "#4caf50" : "#ffffff";
      ctx.fillRect(tgt.x, tgt.y, tgt.w, tgt.h);
      if (projectile) {
        if (projectile.trail.length > 1) {
          ctx.save();
          ctx.strokeStyle = "#888";
          ctx.setLineDash([4, 8]);
          ctx.beginPath();
          ctx.moveTo(projectile.trail[0].x, projectile.trail[0].y);
          projectile.trail.forEach((p) => ctx.lineTo(p.x, p.y));
          ctx.stroke();
          ctx.restore();
        }
        ctx.save();
        ctx.fillStyle = "#ffeb3b";
        ctx.beginPath();
        ctx.arc(
          projectile.pos.x,
          projectile.pos.y,
          BALL_RADIUS,
          0,
          2 * Math.PI
        );
        ctx.fill();
        ctx.strokeStyle = "#fbc02d";
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.restore();
      }
      if (allowShoot && shotsTaken < MAX_SHOTS) {
        ctx.save();
        ctx.fillStyle = "#ffeb3b";
        ctx.beginPath();
        ctx.arc(slingStart.x, slingStart.y, BALL_RADIUS, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = "#fbc02d";
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.restore();
      }
      if (isDragging && dragEnd) {
        ctx.save();
        ctx.strokeStyle = "#d32f2f";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(slingStart.x, slingStart.y);
        ctx.lineTo(dragEnd.x, dragEnd.y);
        ctx.stroke();
        ctx.restore();
      }
      ctx.fillStyle = "#000";
      ctx.font = "16px sans-serif";
      ctx.fillText(`Shots: ${shotsTaken}/${MAX_SHOTS}`, 110, 40);
      if (gameOver) {
        ctx.fillStyle = targetHit ? "#4caf50" : "#f44336";
        ctx.font = "24px sans-serif";
        ctx.fillText(
          targetHit ? "You Win!" : "Game Over",
          canvas.width / 2 - 60,
          50
        );
      }
    }

    (function loop() {
      update();
      render();
      requestAnimationFrame(loop);
    })();
  } catch (err) {
    console.error("Init error:", err);
  }
});
