import pygame
import random
import math
import networkx as nx
from config import *
from enums import *
from entities import Hub, Person

class Engine:
    def __init__(self):
        self.hubs = []
        self.agents = []
        self.view_mode = "SIM" 
        self.tick = 0
        self.day = 0
        self.tick_count = 0
        self.paused = False
        self.history = {'S':[], 'Active':[], 'R':[], 'D':[], 'H':[]}
        self.demographics = {'Child':0, 'Adult':0, 'Senior':0, 'HighMob':0, 'ModMob':0, 'LowMob':0}
        self.init_world()

    def init_world(self):
        self.hubs = []
        self.agents = []
        self.tick = 0
        self.day = 0
        self.tick_count = 0
        self.history = {'S':[], 'Active':[], 'R':[], 'D':[], 'H':[]}
        self.demographics = {'Child':0, 'Adult':0, 'Senior':0, 'HighMob':0, 'ModMob':0, 'LowMob':0}
        
        self.setup_hubs()

        total_pop = int(CONFIG.pop_size)
        for i in range(total_pop):
            home = self.households[i % len(self.households)]
            r = random.random()
            if r < 0.2: age, mob = AgeGroup.CHILD, MobilityType.HIGH
            elif r < 0.75: age, mob = AgeGroup.ADULT, random.choice([MobilityType.HIGH, MobilityType.MODERATE])
            else: age, mob = AgeGroup.SENIOR, MobilityType.LOW
            
            if age == AgeGroup.CHILD: self.demographics['Child'] += 1
            elif age == AgeGroup.ADULT: self.demographics['Adult'] += 1
            else: self.demographics['Senior'] += 1
            
            if mob == MobilityType.HIGH: self.demographics['HighMob'] += 1
            elif mob == MobilityType.MODERATE: self.demographics['ModMob'] += 1
            else: self.demographics['LowMob'] += 1
            
            p = Person(i, home, age, mob)
            
            if age == AgeGroup.CHILD: p.assigned_hub = random.choice(self.schools)
            elif age == AgeGroup.ADULT and mob != MobilityType.LOW: p.assigned_hub = random.choice(self.works)
            else: p.assigned_hub = None 
            
            p.permanent_affiliations.append(home)
            if p.assigned_hub:
                p.permanent_affiliations.append(p.assigned_hub)

            p.structural_edges[home] = 1.0 
            if p.assigned_hub: p.structural_edges[p.assigned_hub] = 0.0
            
            p.structural_edges[self.market] = 0.0
            p.structural_edges[self.hosp] = 0.0
            p.structural_edges[self.quar] = 0.0
            if self.park: p.structural_edges[self.park] = 0.0
            if self.cafe: p.structural_edges[self.cafe] = 0.0
            p.structural_edges[self.cemetery] = 0.0

            self.agents.append(p)

        try:
            G = nx.watts_strogatz_graph(n=total_pop, k=CONFIG.k_neighbors, p=CONFIG.rewire_prob)
        except:
            G = nx.erdos_renyi_graph(n=total_pop, p=0.05)
        
        for u, v in G.edges:
            self.agents[u].graph_neighbors.append(self.agents[v])
            self.agents[v].graph_neighbors.append(self.agents[u])

        seeds = random.sample(self.agents, min(int(CONFIG.init_infected), len(self.agents)))
        for p in seeds:
            self.infect_agent(p)

    def setup_hubs(self):
        self.market = Hub(0, CENTER_X, CENTER_Y, 70, LocationType.MARKET, "MARKET", 400, 1.5)
        self.hubs.append(self.market)
        
        ring_items = [
            (LocationType.SCHOOL, "SCHOOL 1", 300, 2.0),
            (LocationType.SCHOOL, "SCHOOL 2", 300, 2.0),
            (LocationType.WORKPLACE, "OFFICE", 100, 1.2),
            (LocationType.WORKPLACE, "FACTORY", 100, 1.2),
            (LocationType.CAFE, "CAFE", 500, 1.5),
            (LocationType.PARK, "PARK", 800, 0.2)
        ]
        
        self.schools = []
        self.works = []
        self.cafe = None 
        self.park = None 
        
        sim_rad = 180 
        angle_step = (2 * math.pi) / len(ring_items)
        
        for i, (l_type, lbl, cap, risk) in enumerate(ring_items):
            angle = i * angle_step
            sx = CENTER_X + math.cos(angle) * sim_rad
            sy = CENTER_Y + math.sin(angle) * sim_rad
            gx = CENTER_X + math.cos(angle) * RING_RAD_MID
            gy = CENTER_Y + math.sin(angle) * RING_RAD_MID
            
            h = Hub(i+1, sx, sy, 50, l_type, lbl, cap, risk)
            h.graph_pos = pygame.math.Vector2(gx, gy)
            
            if l_type == LocationType.SCHOOL: self.schools.append(h)
            elif l_type == LocationType.WORKPLACE: self.works.append(h)
            elif l_type == LocationType.CAFE: self.cafe = h  
            elif l_type == LocationType.PARK: self.park = h
            self.hubs.append(h)

        hosp = Hub(900, 900, 150, 60, LocationType.HOSPITAL, "HOSPITAL", 50, 0.5)
        hosp.sim_pos = pygame.math.Vector2(SIM_W - 100, 150)
        gx = CENTER_X + math.cos(math.radians(-135)) * RING_RAD_FAR
        gy = CENTER_Y + math.sin(math.radians(-135)) * RING_RAD_FAR
        hosp.graph_pos = pygame.math.Vector2(gx, gy)
        self.hosp = hosp
        self.hubs.append(hosp)
        
        quar = Hub(902, 100, 150, 60, LocationType.QUARANTINE, "QUARANTINE", 200, 0.1)
        quar.sim_pos = pygame.math.Vector2(100, 150)
        gx = CENTER_X + math.cos(math.radians(-45)) * RING_RAD_FAR
        gy = CENTER_Y + math.sin(math.radians(-45)) * RING_RAD_FAR
        quar.graph_pos = pygame.math.Vector2(gx, gy)
        self.quar = quar
        self.hubs.append(quar)
        
        cem = Hub(901, SIM_W - 100, 100, 70, LocationType.CEMETERY, "CEMETERY", 5000, 0.0)
        cem.sim_pos = pygame.math.Vector2(SIM_W - 100, HEIGHT - 100)
        gx = CENTER_X + math.cos(math.radians(45)) * RING_RAD_FAR
        gy = CENTER_Y + math.sin(math.radians(45)) * RING_RAD_FAR
        cem.graph_pos = pygame.math.Vector2(gx, gy)
        self.cemetery = cem
        self.hubs.append(cem)

        self.households = []
        houses_needed = max(10, int(CONFIG.pop_size / 5))
        
        sim_rings = [290, 345, 400] 
        houses_placed = 0
        sim_positions = []
        
        for rad in sim_rings:
            if houses_placed >= houses_needed: break
            circ = 2 * math.pi * rad
            cap = int(circ / (14 * 2.5)) 
            to_place = min(cap, houses_needed - houses_placed)
            angle_step = (2 * math.pi) / to_place if to_place > 0 else 0
            
            for i in range(to_place):
                angle = i * angle_step
                x = CENTER_X + math.cos(angle) * rad
                y = CENTER_Y + math.sin(angle) * rad
                sim_positions.append(pygame.math.Vector2(x, y))
            houses_placed += to_place
            
        graph_angle_step = (2 * math.pi) / len(sim_positions)
        
        for i in range(len(sim_positions)):
            sp = sim_positions[i]
            g_angle = i * graph_angle_step
            gx = CENTER_X + math.cos(g_angle) * RING_RAD_OUTER
            gy = CENTER_Y + math.sin(g_angle) * RING_RAD_OUTER
            
            h = Hub(200+i, sp.x, sp.y, 14, LocationType.HOUSEHOLD, "", 20, 1.5)
            h.sim_pos = sp
            h.graph_pos = pygame.math.Vector2(gx, gy)
            
            self.hubs.append(h)
            self.households.append(h)

    def infect_agent(self, p):
        p.state = State.LATENT
        p.days_in_state = 0
        p.latent_dur = max(0.5, random.gauss(CONFIG.latent_mean, 1.0))
        p.inf_dur = max(2.0, random.gauss(CONFIG.inf_mean, 2.0))
        base_shed = CONFIG.shedding_asymp
        if p.is_superspreader: base_shed *= 3.0
        p.peak_shedding = base_shed 

    def update(self):
        if self.paused: return

        dt_days = DAYS_PER_UPDATE * CONFIG.sim_speed
        
        current_vaxxed = sum(1 for p in self.agents if p.vaccinated)
        target_vaxxed = int(len(self.agents) * CONFIG.vaccine_rate)
        
        if current_vaxxed < target_vaxxed:
            candidates = [p for p in self.agents if not p.vaccinated and p.state == State.SUSCEPTIBLE]
            if candidates:
                to_vax = random.sample(candidates, min(len(candidates), max(1, int(5 * CONFIG.sim_speed))))
                for p in to_vax: p.vaccinated = True
        elif current_vaxxed > target_vaxxed:
            vaxxed = [p for p in self.agents if p.vaccinated]
            to_unvax = random.sample(vaxxed, min(len(vaxxed), max(1, int(5 * CONFIG.sim_speed))))
            for p in to_unvax: p.vaccinated = False

        self.tick_count += 1 * CONFIG.sim_speed
        if self.tick_count >= UPDATES_PER_TICK:
            self.tick_count = 0
            self.tick += 1
            if self.tick > 2:
                self.tick = 0
                self.day += 1
            self.apply_schedule()

        for h in self.hubs: 
            h.agents_present = [] 
            h.temp_viral_load = 0.0 
        
        for p in self.agents:
            p.move_spatial(dt_days)
            if p.current_hub: p.current_hub.agents_present.append(p)
            
        self.apply_spring_physics()
        for p in self.agents:
            p.update_physics()

        self.process_graph_transmission(dt_days)

        self.hosp.occupied_beds = sum(1 for p in self.agents if p.state == State.HOSPITALIZED)
        for p in self.agents:
            self.update_bio(p, dt_days)

        if int(self.tick_count) % 40 == 0:
            c = {'S':0, 'Active':0, 'R':0, 'D':0, 'H':0}
            for p in self.agents:
                if p.state == State.SUSCEPTIBLE: c['S']+=1
                elif p.state in [State.LATENT, State.INF_ASYMP, State.INF_SYMP]: c['Active']+=1
                elif p.state == State.HOSPITALIZED: 
                    c['Active']+=1
                    c['H']+=1
                elif p.state == State.RECOVERED: c['R']+=1
                elif p.state == State.DEAD: c['D']+=1
            for k, v in c.items(): self.history[k].append(v)
            if len(self.history['S']) > PANEL_W - 40:
                for k in self.history: self.history[k].pop(0)

    def safe_normalize(self, v):
        if v.length_squared() < 0.0001:
            return pygame.math.Vector2(random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1))
        return v.normalize()

    def apply_spring_physics(self):
        grid_size = 60
        grid = {}
        for p in self.agents:
            k = (int(p.graph_pos.x/grid_size), int(p.graph_pos.y/grid_size))
            if k not in grid: grid[k] = []
            grid[k].append(p)
            
        for p in self.agents:
            # 1. Structural
            for hub in p.permanent_affiliations:
                diff = hub.graph_pos - p.graph_pos
                dist = diff.length()
                if dist > 0:
                    k_val = K_HOME if hub.type == LocationType.HOUSEHOLD else K_WORK
                    force = self.safe_normalize(diff) * ((dist - L_STRUCT) * k_val)
                    p.acc += force

            # 2. Social
            for friend in p.graph_neighbors:
                diff = friend.graph_pos - p.graph_pos
                dist = diff.length()
                if dist > 0:
                    force = self.safe_normalize(diff) * ((dist - L_SOCIAL) * K_SOCIAL)
                    p.acc += force
            
            # 3. Repulsion
            gx, gy = int(p.graph_pos.x/grid_size), int(p.graph_pos.y/grid_size)
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    neighbors = grid.get((gx+dx, gy+dy), [])
                    for other in neighbors:
                        if p == other: continue
                        diff = p.graph_pos - other.graph_pos
                        dist_sq = diff.length_squared()
                        if dist_sq < 1: dist_sq = 1
                        if dist_sq > 2500: continue 
                        strength = REPULSION_STRENGTH
                        if p.home == other.home: strength *= 0.1 
                        force_mag = strength / dist_sq
                        p.acc += self.safe_normalize(diff) * force_mag

    def process_graph_transmission(self, dt):
        for p in self.agents:
            shedding = p.get_shedding()
            if shedding > 0:
                for hub, weight in p.structural_edges.items():
                    if weight > 0.1:
                        hub.temp_viral_load += (shedding * weight)
        
        distancing_factor = 1.0
        if CONFIG.social_engagement < 0.4:
            distancing_factor = 0.2 
        
        for p in self.agents:
            if p.state != State.SUSCEPTIBLE: continue
            
            for hub, weight in p.structural_edges.items():
                if weight > 0.1 and hub.temp_viral_load > 0:
                    risk = (hub.temp_viral_load / (hub.capacity + 1)) 
                    risk *= hub.risk_mult * CONFIG.beta * 0.5 * distancing_factor * weight
                    prob = 1.0 - math.exp(-risk * dt)
                    self.try_infect(p, prob)

        infectors = [p for p in self.agents if p.get_shedding() > 0]
        for infector in infectors:
            shedding = infector.get_shedding()
            for neighbor in infector.graph_neighbors:
                if neighbor.state != State.SUSCEPTIBLE: continue
                
                prob_val = shedding * CONFIG.beta * distancing_factor
                dist = infector.sim_pos.distance_to(neighbor.sim_pos)
                decay = 1.0 / (1.0 + (dist / CONFIG.kappa) ** 2)
                
                if infector.current_hub and neighbor.current_hub:
                     if infector.current_hub == neighbor.current_hub:
                         prob_val *= 5.0 
                
                final_prob = 1.0 - math.exp(-prob_val * decay * dt)
                self.try_infect(neighbor, final_prob)

    def try_infect(self, target, prob):
        sus_factor = 1.0 - (target.immunity * CONFIG.immunity_efficacy + target.constitution * 0.2)
        if target.vaccinated: sus_factor *= (1.0 - CONFIG.vaccine_efficacy)
        if target.masked: sus_factor *= (1.0 - CONFIG.mask_efficacy)
        if random.random() < prob * max(0, sus_factor):
            self.infect_agent(target)

    def update_bio(self, p, dt):
        if p.immunity > 0:
            p.immunity *= math.exp(-CONFIG.immunity_waning * dt)
            if p.immunity < 0.2 and p.state == State.RECOVERED:
                p.state = State.SUSCEPTIBLE
                p.immunity = 0.0
        
        if p.state == State.DEAD: return
        p.days_in_state += dt

        if p.state == State.LATENT:
            if p.days_in_state >= p.latent_dur:
                p.state = State.INF_SYMP
                prob_asymp = CONFIG.asymp_prob
                if p.vaccinated: prob_asymp += 0.4
                if p.age == AgeGroup.CHILD: prob_asymp += 0.2
                if p.age == AgeGroup.SENIOR: prob_asymp -= 0.2
                
                if random.random() < prob_asymp:
                    p.state = State.INF_ASYMP
                    p.peak_shedding = CONFIG.shedding_asymp
                else:
                    p.state = State.INF_SYMP
                    p.peak_shedding = CONFIG.shedding_symp
                    if not p.in_quarantine and random.random() < CONFIG.quarantine_rate:
                        p.in_quarantine = True
                        p.set_target(self.quar)
                if p.is_superspreader: p.peak_shedding *= 3.0
                p.days_in_state = 0
        
        elif p.state in [State.INF_SYMP, State.INF_ASYMP, State.HOSPITALIZED]:
            if p.state == State.INF_SYMP and p.days_in_state > 2.0:
                if p.constitution < 0.4 or p.age == AgeGroup.SENIOR:
                    if p.state != State.HOSPITALIZED:
                        if self.hosp.occupied_beds < self.hosp.capacity:
                            p.state = State.HOSPITALIZED
                            p.in_quarantine = False 
                            p.set_target(self.hosp)
                            p.hospital_stay_dur = max(2.0, random.gauss(CONFIG.hosp_stay_mean, 2.0))

            hazard = CONFIG.base_mortality
            if p.vaccinated: hazard *= 0.1
            if p.state == State.HOSPITALIZED: hazard *= CONFIG.hosp_mortality_mult
            elif p.state == State.INF_SYMP and (p.constitution < 0.4 or p.age == AgeGroup.SENIOR):
                 if self.hosp.occupied_beds >= self.hosp.capacity: hazard *= CONFIG.no_bed_mult
            if p.age == AgeGroup.SENIOR: hazard *= 3.0
            if p.age == AgeGroup.CHILD: hazard *= 0.1
            
            p_die = 1.0 - math.exp(-hazard * dt)
            if random.random() < p_die:
                p.state = State.DEAD
                p.in_quarantine = False
                p.set_target(self.cemetery)
            elif p.days_in_state >= p.inf_dur:
                p.state = State.RECOVERED
                p.immunity = 1.0
                p.in_quarantine = False
                if p.current_hub == self.hosp or p.current_hub == self.quar: p.set_target(p.home)

    def apply_schedule(self):
        is_weekend = (self.day % 7) >= 5
        social = CONFIG.social_engagement
        is_lockdown = social < 0.4
        
        for p in self.agents:
            if p.state == State.DEAD: 
                p.set_target(self.cemetery)
                continue
            if p.state == State.HOSPITALIZED:
                p.set_target(self.hosp) 
                continue
            if p.in_quarantine:
                p.set_target(self.quar)
                continue
            if p.state == State.INF_SYMP:
                p.set_target(p.home)
                continue

            if self.tick == 0: 
                if is_weekend:
                    if random.random() < (0.5 * social):
                        r = random.random()
                        if r < 0.4: p.set_target(self.park)
                        elif r < 0.7: p.set_target(self.market)
                        else: p.set_target(self.cafe)
                    else:
                        p.set_target(p.home)
                else:
                    if is_lockdown:
                        if random.random() < 0.02: p.set_target(self.market)
                        else: p.set_target(p.home)
                    else:
                        if p.age == AgeGroup.SENIOR or p.mobility == MobilityType.LOW:
                            if random.random() < 0.15: p.set_target(self.market)
                            else: p.set_target(p.home)
                        elif p.assigned_hub:
                            if random.random() < 0.95: p.set_target(p.assigned_hub)
                            else: p.set_target(p.home)
                        else:
                            p.set_target(p.home)
            elif self.tick == 1:
                if is_lockdown:
                    p.set_target(p.home)
                else:
                    if p.mobility == MobilityType.HIGH and random.random() < (0.3 * social): p.set_target(self.cafe)
                    elif random.random() < (0.2 * social): p.set_target(random.choice(self.households)) 
                    elif random.random() < (0.2 * social): p.set_target(self.market)
                    else: p.set_target(p.home)
            elif self.tick == 2:
                p.set_target(p.home)