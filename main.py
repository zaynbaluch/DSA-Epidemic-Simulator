import pygame
from config import WIDTH, HEIGHT, SIM_W, CENTER_X, CENTER_Y, C_BG, C_EDGE_STATIC, RING_RAD_MID, RING_RAD_OUTER, FPS
from enums import LocationType, State
from engine import Engine
from ui import UI

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DSA Final Project: Complete Graph Vis")
    clock = pygame.time.Clock()
    
    engine = Engine()
    ui = UI(engine)
    
    graph_surf = pygame.Surface((SIM_W, HEIGHT), pygame.SRCALPHA)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            for s in ui.sliders: 
                if s.handle(event): pass
            ui.btn_reset.handle(event)
            ui.btn_pause.handle(event)
            ui.btn_view.handle(event)
            
        ui.update()
        engine.update()
        
        screen.fill(C_BG)
        
        if engine.view_mode == "SIM":
            for h in engine.households:
                 pygame.draw.line(screen, (20,25,30), h.sim_pos, engine.market.sim_pos, 1)
            for h in engine.hubs: h.draw(screen, "SIM")
        else:
            graph_surf.fill((0,0,0,0))
            center = (CENTER_X, CENTER_Y)
            pygame.draw.circle(graph_surf, (25, 30, 35, 100), center, RING_RAD_MID, 1)
            pygame.draw.circle(graph_surf, (25, 30, 35, 100), center, RING_RAD_OUTER, 1)
            
            for p in engine.agents:
                for hub in p.permanent_affiliations:
                    if hub.type == LocationType.HOUSEHOLD:
                        pygame.draw.line(graph_surf, C_EDGE_STATIC, p.graph_pos, hub.graph_pos, 1)

            for p in engine.agents:
                for hub, weight in p.structural_edges.items():
                    if hub.type == LocationType.HOUSEHOLD: continue 
                    if weight < 0.05: continue
                    
                    start = p.graph_pos
                    end = hub.graph_pos
                    
                    base_col = (100, 100, 100)
                    if hub.type == LocationType.MARKET: base_col = (200, 150, 50) 
                    elif hub.type == LocationType.PARK: base_col = (50, 200, 50) 
                    elif hub.type == LocationType.HOSPITAL: base_col = (200, 50, 200) 
                    elif hub.type == LocationType.QUARANTINE: base_col = (200, 200, 50)
                    elif hub.type == LocationType.CEMETERY: base_col = (200, 200, 200) 
                    elif hub.type == LocationType.SCHOOL: base_col = (50, 100, 200) 
                    elif hub.type == LocationType.WORKPLACE: base_col = (200, 100, 50) 
                    
                    alpha = int(255 * weight)
                    col = (*base_col, alpha)
                    width = 2 if weight > 0.8 else 1
                    pygame.draw.line(graph_surf, col, start, end, width)

            for p in engine.agents:
                for friend in p.graph_neighbors:
                    if p.id < friend.id: 
                        col = C_EDGE_STATIC 
                        width = 1
                        if (p.state in [State.INF_SYMP, State.INF_ASYMP] and friend.state == State.SUSCEPTIBLE) or \
                           (friend.state in [State.INF_SYMP, State.INF_ASYMP] and p.state == State.SUSCEPTIBLE):
                            col = (255, 50, 50, 200) 
                            width = 2
                        pygame.draw.line(graph_surf, col, p.graph_pos, friend.graph_pos, width)
            
            screen.blit(graph_surf, (0,0))
            for h in engine.hubs: h.draw(screen, "GRAPH")
        
        for p in engine.agents: p.draw(screen, engine.view_mode)
        
        ui.draw_hud(screen, engine)
        ui.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()