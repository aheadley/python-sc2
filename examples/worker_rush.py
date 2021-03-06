import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer

class WorkerRushBot(sc2.BotAI):
    async def on_step(self, state, iteration):
        if iteration == 0:
            for probe in self.workers:
                await self.do(probe.attack(self.enemy_start_locations[0]))

def main():
    run_game(maps.get("Abyssal Reef LE"), [
        Bot(Race.Protoss, WorkerRushBot()),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=True)

if __name__ == '__main__':
    main()
