import pyxel
import math

class Particle:
    def __init__(self, x, y, dx, dy, life, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.life = life
        self.color = color
        self.original_life = life

class Planet:
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.collected = False
        self.orbit_angle = 0

class SpaceExplorer:
    def __init__(self):
        # 画面サイズの定数
        self.WIDTH = 160
        self.HEIGHT = 120
        
        # ゲームの初期化
        pyxel.init(self.WIDTH, self.HEIGHT, title="Space Explorer")
        self.reset_game()
        # ゲーム開始
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        # プレイヤーの初期化
        self.player_x = 80
        self.player_y = 100
        self.player_dx = 0
        self.player_dy = 0
        self.energy = 100
        self.thrust_particles = []
        
        # 星の位置を初期化
        self.stars = []
        for _ in range(50):
            self.stars.append([pyxel.rndi(0, 159), pyxel.rndi(0, 119)])
        
        # 惑星の初期化
        self.planets = []
        planet_colors = [8, 9, 10, 11, 12]
        for i in range(5):
            self.planets.append(Planet(
                pyxel.rndi(20, 140),
                pyxel.rndi(20, 100),
                planet_colors[i],
                pyxel.rndi(2, 4)
            ))
        
        # パーティクルの初期化
        self.particles = []
        
        # 流れ星の初期化
        self.shooting_stars = []
        
        # ゲーム状態の初期化
        self.score = 0
        self.game_over = False
        self.game_clear = False
        self.collected_planets = 0
        self.level = 1
        self.win_effects_timer = 0

    def create_explosion(self, x, y, color):
        for _ in range(20):
            angle = pyxel.rndf(0, math.pi * 2)
            speed = pyxel.rndf(0.5, 2)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            self.particles.append(Particle(x, y, dx, dy, 30, color))

    def create_win_effect(self):
        for _ in range(10):
            x = pyxel.rndi(0, 160)
            y = pyxel.rndi(0, 120)
            color = pyxel.rndi(8, 12)
            self.create_explosion(x, y, color)

    def add_thrust_particle(self):
        angle = pyxel.rndf(math.pi/4, 3*math.pi/4)
        speed = pyxel.rndf(0.5, 2)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        x = self.player_x + pyxel.rndi(-2, 2)
        y = self.player_y + 5
        self.thrust_particles.append(Particle(x, y, dx, dy, 15, 8 + pyxel.rndi(0, 2)))

    def update(self):
        if self.game_over or self.game_clear:
            if pyxel.btnp(pyxel.KEY_R):
                self.reset_game()
            if self.game_clear:
                self.win_effects_timer += 1
                if self.win_effects_timer % 30 == 0:
                    self.create_win_effect()
            return

        self.update_player()
        self.update_particles()
        self.update_planets()
        self.update_stars()
        self.update_shooting_stars()
        self.check_collisions()
        
        # エネルギー消費
        self.energy = max(0, self.energy - 0.1)
        if self.energy <= 0:
            self.game_over = True
            self.create_explosion(self.player_x, self.player_y, 8)

        # クリア判定
        if self.collected_planets >= 5:
            self.game_clear = True
            self.create_win_effect()

    def update_player(self):
        # プレイヤーの移動（慣性あり）
        acceleration = 0.5 if self.energy > 0 else 0.1
        deceleration = 0.95

        if pyxel.btn(pyxel.KEY_LEFT):
            self.player_dx -= acceleration
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.player_dx += acceleration
        if pyxel.btn(pyxel.KEY_UP):
            self.player_dy -= acceleration
            if pyxel.frame_count % 2 == 0:
                self.add_thrust_particle()
        if pyxel.btn(pyxel.KEY_DOWN):
            self.player_dy += acceleration

        # 速度の制限
        max_speed = 3
        self.player_dx = max(min(self.player_dx, max_speed), -max_speed)
        self.player_dy = max(min(self.player_dy, max_speed), -max_speed)

        # 慣性による減速
        self.player_dx *= deceleration
        self.player_dy *= deceleration

        # 位置の更新
        self.player_x += self.player_dx
        self.player_y += self.player_dy

        # 画面端での跳ね返り
        if self.player_x < 0 or self.player_x > self.WIDTH - 1:
            self.player_dx *= -0.7
            self.player_x = max(0, min(self.player_x, self.WIDTH - 1))
        if self.player_y < 0 or self.player_y > self.HEIGHT - 1:
            self.player_dy *= -0.7
            self.player_y = max(0, min(self.player_y, self.HEIGHT - 1))

    def update_particles(self):
        # パーティクルの更新
        for particle in self.particles[:]:
            particle.x += particle.dx
            particle.y += particle.dy
            particle.life -= 1
            if particle.life <= 0:
                self.particles.remove(particle)

        # 推進パーティクルの更新
        for particle in self.thrust_particles[:]:
            particle.x += particle.dx
            particle.y += particle.dy
            particle.life -= 1
            if particle.life <= 0:
                self.thrust_particles.remove(particle)

    def update_planets(self):
        # 惑星の軌道更新
        for planet in self.planets:
            if not planet.collected:
                planet.orbit_angle += 0.02
                planet.y += math.sin(planet.orbit_angle) * 0.5

    def update_stars(self):
        # 星の点滅
        if pyxel.frame_count % 30 == 0:
            for i in range(len(self.stars)):
                if pyxel.rndf(0, 1) > 0.2:
                    continue
                self.stars[i] = [pyxel.rndi(0, 159), pyxel.rndi(0, 119)]

    def update_shooting_stars(self):
        # 流れ星の生成
        if pyxel.frame_count % 60 == 0 and pyxel.rndf(0, 1) < 0.3:
            self.shooting_stars.append([0, pyxel.rndi(0, 40)])
        
        # 流れ星の移動
        new_stars = []
        for star in self.shooting_stars:
            star[0] += 2
            star[1] += 1
            if star[0] <= 160 and star[1] <= 120:
                new_stars.append(star)
        self.shooting_stars = new_stars

    def check_collisions(self):
        # 惑星との衝突判定
        for planet in self.planets:
            if not planet.collected:
                dx = self.player_x - planet.x
                dy = self.player_y - planet.y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance < planet.size * 3:
                    planet.collected = True
                    self.collected_planets += 1
                    self.score += 1000
                    self.energy = min(100, self.energy + 30)
                    self.create_explosion(planet.x, planet.y, planet.color)

    def draw_centered_text(self, y, text, color):
        """中央揃えでテキストを描画"""
        x = (self.WIDTH - len(text) * 4) // 2  # 4は文字の幅
        pyxel.text(x, y, text, color)

    def draw_status_text(self, y, label, value, color):
        """ステータステキストを描画（左揃え、位置固定）"""
        margin = 10
        pyxel.text(margin, y, f"{label}: {value}", color)

    def draw(self):
        pyxel.cls(0)
        
        # 背景の星を描画
        for star_x, star_y in self.stars:
            pyxel.pset(star_x, star_y, 7)
        
        # 流れ星の描画
        for star in self.shooting_stars:
            pyxel.line(star[0], star[1], star[0]-4, star[1]-2, 8)

        # パーティクルの描画
        for particle in self.thrust_particles + self.particles:
            pyxel.pset(int(particle.x), int(particle.y), particle.color)

        # 惑星の描画
        for planet in self.planets:
            if not planet.collected:
                pyxel.circ(int(planet.x), int(planet.y), planet.size, planet.color)
                # 惑星の軌道を示す点線
                for i in range(8):
                    angle = i * math.pi / 4
                    orbit_x = int(planet.x + math.cos(angle) * 8)
                    orbit_y = int(planet.y + math.sin(angle) * 8)
                    pyxel.pset(orbit_x, orbit_y, 1)

        # プレイヤー（宇宙船）の描画
        if not self.game_over:
            pyxel.tri(
                self.player_x, self.player_y - 4,
                self.player_x - 3, self.player_y + 4,
                self.player_x + 3, self.player_y + 4,
                11 if self.energy > 30 else 8
            )

        # ステータス情報の描画（シンプルに表示）
        self.draw_status_text(5, "SCORE", str(self.score).zfill(5), 7)
        self.draw_status_text(13, "ENERGY", f"{int(self.energy)}%", 11 if self.energy > 30 else 8)
        self.draw_status_text(21, "PLANETS", f"{self.collected_planets}/5", 12)

        # ゲームオーバー画面
        if self.game_over and not self.game_clear:
            # 背景を暗く
            for y in range(0, self.HEIGHT, 2):
                for x in range(0, self.WIDTH, 2):
                    pyxel.pset(x, y, 0)
            
            center_y = self.HEIGHT // 2
            self.draw_centered_text(center_y - 10, "GAME OVER", 8)
            self.draw_centered_text(center_y + 10, "PRESS R TO RESTART", 7)

        # 勝利画面
        if self.game_clear:
            # 背景を暗く
            for y in range(0, self.HEIGHT, 2):
                for x in range(0, self.WIDTH, 2):
                    pyxel.pset(x, y, 0)
            
            center_y = self.HEIGHT // 2
            
            # 点滅効果付きのCONGRATULATIONS
            if pyxel.frame_count % 30 < 20:
                self.draw_centered_text(center_y - 20, "CONGRATULATIONS!", 11)
            
            # 虹色に変化するYOU WIN!
            self.draw_centered_text(center_y - 5, "YOU WIN!", (pyxel.frame_count // 4) % 16)
            
            # リスタート指示
            self.draw_centered_text(center_y + 10, "PRESS R TO RESTART", 7)
            
            # スコア表示
            score_text = f"FINAL SCORE: {str(self.score).zfill(5)}"
            self.draw_centered_text(center_y + 25, score_text, 10)

# ゲームの開始
SpaceExplorer()