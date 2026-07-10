"""
Genetic Algorithm optimization for timetable improvement using DEAP.
"""
import random
from deap import base, creator, tools, algorithms

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

class GeneticOptimizer:
    def __init__(self, variables, population_size=100, generations=50):
        self.variables = variables
        self.population_size = population_size
        self.generations = generations
        self.toolbox = base.Toolbox()
        self._setup()

    def _setup(self):
        self.toolbox.register("attr_day", random.randint, 0, 5)
        self.toolbox.register("attr_period", random.randint, 0, 7)
        self.toolbox.register("individual", tools.initCycle, creator.Individual,
                              (self.toolbox.attr_day, self.toolbox.attr_period),
                              n=len(self.variables) * 2)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self.evaluate)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutUniformInt, low=0, high=5, indpb=0.05)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

    def evaluate(self, individual):
        assignments = []
        for i in range(0, len(individual), 2):
            assignments.append((individual[i], individual[i+1]))
        violations = 0
        for idx, var in enumerate(self.variables):
            day, period = assignments[idx]
            teacher = var.get('teacher')
            if teacher:
                if teacher.preferred_days and day not in teacher.preferred_days:
                    violations += 1
                if teacher.preferred_periods and period not in teacher.preferred_periods:
                    violations += 1
        return (violations,)

    def improve(self, initial_solution):
        initial_individual = []
        for day, period in initial_solution:
            initial_individual.extend([day, period])
        pop = self.toolbox.population(n=self.population_size-1)
        pop.append(creator.Individual(initial_individual))
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", lambda x: sum(f[0] for f in x)/len(x))
        stats.register("min", min)
        pop, log = algorithms.eaSimple(pop, self.toolbox, cxpb=0.5, mutpb=0.2, ngen=self.generations,
                                       stats=stats, halloffame=hof, verbose=False)
        best = hof[0]
        return [(best[i], best[i+1]) for i in range(0, len(best), 2)]