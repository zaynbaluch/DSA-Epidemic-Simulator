import pygame
from config import SIM_W, PANEL_W, HEIGHT, C_TEXT, C_TEXT_DIM, C_ACCENT, C_PANEL, C_BORDER, CONFIG, COLORS
from enums import State

class Slider:
    def __init__(self, x, y, w, min_v, max_v, init, label, precision=1):
        self.rect = pygame.Rect(x, y, w, 6)
        self.min = min_v
        self.max = max_v
        self.val = init
        self.label = label
        self.prec = precision
        self.dragging = False
        self.font = pygame.font.SysFont("Consolas", 12)

    def handle(self, event):
        mx, my = pygame.mouse.get_pos()
        adj_mx = mx - SIM_W
        hit = self.rect.inflate(0, 14)
        if event.type == pygame.MOUSEBUTTONDOWN and hit.collidepoint(adj_mx, my):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False  
        if self.dragging:
            r = (adj_mx - self.rect.x) / self.rect.w
            self.val = self.min + max(0, min(1, r)) * (self.max - self.min)
            return True
        return False

    def draw(self, surface, ox, oy):
        val_str = f"{self.val:.{self.prec}f}"
        lbl = self.font.render(f"{self.label}: {val_str}", True, C_TEXT_DIM)
        surface.blit(lbl, (ox+self.rect.x, oy+self.rect.y-15))
        pygame.draw.rect(surface, (40,45,50), (ox+self.rect.x, oy+self.rect.y, self.rect.w, self.rect.h), border_radius=3)
        pct = (self.val - self.min) / (self.max - self.min)
        pygame.draw.rect(surface, C_ACCENT, (ox+self.rect.x, oy+self.rect.y, pct*self.rect.w, self.rect.h), border_radius=3)
        kx = int(ox+self.rect.x+pct*self.rect.w)
        ky = int(oy+self.rect.centery)
        pygame.draw.circle(surface, C_TEXT, (kx, ky), 5)

class Button:
    def __init__(self, x, y, w, h, text, cb):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.cb = cb
        self.hover = False
        self.font = pygame.font.SysFont("Verdana", 11, bold=True)
    def handle(self, e):
        mx, my = pygame.mouse.get_pos()
        if e.type == pygame.MOUSEMOTION: self.hover = self.rect.collidepoint(mx-SIM_W, my)
        if e.type == pygame.MOUSEBUTTONDOWN and self.hover: self.cb()
    def draw(self, s, ox, oy):
        r = pygame.Rect(ox+self.rect.x, oy+self.rect.y, self.rect.w, self.rect.h)
        col = (60,120,180) if self.hover else (50,60,70)
        pygame.draw.rect(s, col, r, border_radius=4)
        pygame.draw.rect(s, C_ACCENT, r, 1, border_radius=4)
        t = self.font.render(self.text, True, C_TEXT)
        s.blit(t, (r.centerx-t.get_width()//2, r.centery-t.get_height()//2))

class UI:
    def __init__(self, engine):
        self.engine = engine
        self.font = pygame.font.SysFont("Consolas", 14)
        self.font_lg = pygame.font.SysFont("Verdana", 16, bold=True)
        
        self.sliders = [
            Slider(20, 60, 180, 200, 2000, CONFIG.pop_size, "Population", 0),
            Slider(20, 100, 180, 1, 50, CONFIG.init_infected, "Initial Cases", 0),
            Slider(20, 140, 180, 0.0, 100.0, CONFIG.beta, "Beta (Infectivity)", 1), 
            Slider(20, 180, 180, 1.0, 100.0, CONFIG.kappa, "Dist Decay (Kappa)", 1),
            Slider(20, 220, 180, 0.0, 2.0, CONFIG.social_engagement, "Social Engagement", 2),
            Slider(20, 260, 180, 0.0, 1.0, CONFIG.mask_compliance, "Mask Compliance", 2),
            Slider(20, 300, 180, 0.0, 1.0, CONFIG.vaccine_rate, "Vaccination Rate", 2), 
            Slider(230, 60, 180, 0.1, 20.0, CONFIG.sim_speed, "Time Warp", 1),
            Slider(230, 100, 180, 2, 30, CONFIG.inf_mean, "Infectious Days", 1),
            Slider(230, 140, 180, 2, 21, CONFIG.hosp_stay_mean, "Hospital Stay", 1),
            Slider(230, 180, 180, 0.0, 0.20, CONFIG.base_mortality, "Base Mortality/Day", 3),
            Slider(230, 220, 180, 0.0, 1.0, CONFIG.quarantine_rate, "Quar. Rate", 2),
        ]
        
        self.btn_reset = Button(20, 340, 100, 30, "RESET", self.reset)
        self.btn_pause = Button(130, 340, 100, 30, "PAUSE", self.pause)
        self.btn_view = Button(240, 340, 120, 30, "VIEW MODE", self.toggle_view)

    def reset(self):
        self.sliders[6].val = 0.0
        CONFIG.vaccine_rate = 0.0
        CONFIG.pop_size = self.sliders[0].val
        CONFIG.init_infected = self.sliders[1].val
        self.engine.init_world()

    def pause(self): 
        self.engine.paused = not self.engine.paused
        
    def toggle_view(self):
        self.engine.view_mode = "GRAPH" if self.engine.view_mode == "SIM" else "SIM"

    def update(self):
        CONFIG.beta = self.sliders[2].val
        CONFIG.kappa = self.sliders[3].val
        CONFIG.social_engagement = self.sliders[4].val
        CONFIG.mask_compliance = self.sliders[5].val
        CONFIG.vaccine_rate = self.sliders[6].val
        CONFIG.sim_speed = self.sliders[7].val
        CONFIG.inf_mean = self.sliders[8].val
        CONFIG.hosp_stay_mean = self.sliders[9].val
        CONFIG.base_mortality = self.sliders[10].val
        CONFIG.quarantine_rate = self.sliders[11].val

    def draw(self, surface):
        ox = SIM_W
        pygame.draw.rect(surface, C_PANEL, (ox, 0, PANEL_W, HEIGHT))
        pygame.draw.line(surface, C_ACCENT, (ox, 0), (ox, HEIGHT), 2)
        surface.blit(self.font_lg.render("DSA Disease Spread Simulator", True, C_ACCENT), (ox+20, 15))
        
        for s in self.sliders: s.draw(surface, ox, 0)
        self.btn_reset.draw(surface, ox, 0)
        self.btn_pause.draw(surface, ox, 0)
        self.btn_view.draw(surface, ox, 0)
        
        mode_txt = f"MODE: {self.engine.view_mode}"
        col = C_ACCENT if self.engine.view_mode == "GRAPH" else (200, 200, 200)
        surface.blit(self.font_lg.render(mode_txt, True, col), (ox+240, 375))
        
        y = 400
        c = {k:0 for k in COLORS}
        vax_count = 0
        for p in self.engine.agents: 
            if p.vaccinated: vax_count += 1
            k='S'
            if p.state == State.LATENT: k='L'
            elif p.state == State.INF_ASYMP: k='IA'
            elif p.state == State.INF_SYMP: k='IS'
            elif p.state == State.HOSPITALIZED: k='H'
            elif p.state == State.RECOVERED: k='R'
            elif p.state == State.DEAD: k='D'
            c[k]+=1
        
        lines = [
            (f"Susceptible: {c['S']}", COLORS['S']),
            (f"Vaccinated: {vax_count}", COLORS['V']),
            (f"Latent: {c['L']}", COLORS['L']),
            (f"Infectious: {c['IA']+c['IS']}", COLORS['IS']),
            (f"Hospitalized: {c['H']} / {self.engine.hosp.capacity}", COLORS['H']),
            (f"Recovered: {c['R']}", COLORS['R']),
            (f"Dead: {c['D']}", COLORS['D'])
        ]
        
        for txt, col in lines:
            pygame.draw.circle(surface, col, (ox+20, y+8), 5)
            surface.blit(self.font.render(txt, True, C_TEXT), (ox+35, y))
            y += 20
        
        y_dem = 550
        surface.blit(self.font_lg.render("DEMOGRAPHICS", True, C_TEXT), (ox+20, y_dem))
        y_dem += 25
        d = self.engine.demographics
        demo_txt = [
            f"Children: {d['Child']}  Adults: {d['Adult']}  Seniors: {d['Senior']}",
            f"Mobility: High({d['HighMob']}) Mod({d['ModMob']}) Low({d['LowMob']})"
        ]
        for txt in demo_txt:
            surface.blit(self.font.render(txt, True, C_TEXT_DIM), (ox+20, y_dem))
            y_dem += 20

        gw, gh = PANEL_W - 40, 200
        gy = HEIGHT - 220
        gx = ox + 20
        pygame.draw.rect(surface, (15,18,22), (gx, gy, gw, gh))
        pygame.draw.rect(surface, C_BORDER, (gx, gy, gw, gh), 1)
        
        hist = self.engine.history
        if len(hist['S']) > 2:
            max_p = max(1, len(self.engine.agents))
            series = [('S', COLORS['S']), ('Active', COLORS['IS']), ('H', COLORS['H']), ('R', COLORS['R']), ('D', COLORS['D'])]
            for key, col in series:
                pts = []
                data = hist[key]
                step_x = gw / max(1, len(data)-1)
                for i, v in enumerate(data):
                    px = gx + i * step_x
                    py = (gy + gh) - (v / max_p) * gh
                    pts.append((px, py))
                if len(pts) > 1: pygame.draw.lines(surface, col, False, pts, 2)

    def draw_hud(self, surface, engine):
        mx = SIM_W // 2
        y = 30
        phases = ["MORNING", "EVENING", "NIGHT"]
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        day_name = days[engine.day % 7]
        
        txt = self.font_lg.render(f"DAY {engine.day} ({day_name}) | {phases[engine.tick]}", True, (200, 200, 200))
        pill = txt.get_rect(center=(mx, y)).inflate(40, 16)
        pygame.draw.rect(surface, (30,30,40), pill, border_radius=15)
        pygame.draw.rect(surface, (60,60,70), pill, 1, border_radius=15)
        surface.blit(txt, txt.get_rect(center=(mx, y)))