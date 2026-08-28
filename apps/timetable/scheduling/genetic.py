"""
Genetic Algorithm optimization for timetable improvement using DEAP.
"""
import random
import logging
from collections import defaultdict

from deap import base, creator, tools, algorithms

logger = logging.getLogger(__name__)

# Safe DEAP creator setup (idempotent for hot-reloads)
try:
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
except RuntimeError:
    pass  # Already registered from a previous import


class GeneticOptimizer:
    def __init__(self, tasks, max_period=7, population_size=100, generations=50):
        """
        tasks        : List[Task] or List[dict] — ALL tasks (single + combined)
        max_period   : Highest period_number in the school (e.g. 7 or 8)
        """
        self.tasks = tasks
        self.n = len(tasks)
        self.max_period = max_period
        self.population_size = population_size
        self.generations = generations
        self.toolbox = base.Toolbox()
        self._setup()

    def _setup(self):
        self.toolbox.register("attr_day", random.randint, 0, 5)
        self.toolbox.register("attr_period", random.randint, 0, self.max_period)
        self.toolbox.register(
            "individual",
            tools.initCycle,
            creator.Individual,
            (self.toolbox.attr_day, self.toolbox.attr_period),
            n=self.n,
        )
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self.evaluate)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self._mutate)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

    def _mutate(self, individual):
        for i in range(0, len(individual), 2):
            if random.random() < 0.1:
                individual[i] = random.randint(0, 5)
            if random.random() < 0.1:
                individual[i + 1] = random.randint(0, self.max_period)
        return individual,

    def _teacher(self, task):
        if hasattr(task, "teacher"):
            return task.teacher
        return task.get("teacher")

    def _section_ids(self, task):
        if hasattr(task, "target_sections") and task.target_sections:
            return [s.id for s in task.target_sections]
        if hasattr(task, "section_id"):
            return [task.section_id]
        return [task.get("section_id")]

    def evaluate(self, individual):
        assignments = [(individual[i * 2], individual[i * 2 + 1]) for i in range(self.n)]
        violations = 0

        teacher_slots = defaultdict(list)
        for i, task in enumerate(self.tasks):
            t = self._teacher(task)
            if t:
                teacher_slots[(t.id, assignments[i])].append(i)
        for dup in teacher_slots.values():
            if len(dup) > 1:
                violations += (len(dup) - 1) * 1000

        section_slots = defaultdict(list)
        for i, task in enumerate(self.tasks):
            for sid in self._section_ids(task):
                section_slots[(sid, assignments[i])].append(i)
        for dup in section_slots.values():
            if len(dup) > 1:
                violations += (len(dup) - 1) * 1000

        for i, task in enumerate(self.tasks):
            day, period = assignments[i]
            t = self._teacher(task)
            if not t:
                continue
            pref_days = getattr(t, "preferred_days", None)
            pref_periods = getattr(t, "preferred_periods", None)
            if pref_days and day not in pref_days:
                violations += 1
            if pref_periods and period not in pref_periods:
                violations += 1

        return (violations,)

    def improve(self, initial_solution):
        if len(initial_solution) != self.n:
            logger.warning(
                f"GA seed length mismatch: {len(initial_solution)} vs {self.n} tasks. "
                f"Padding/truncating."
            )
            initial_solution = list(initial_solution)[:self.n]
            while len(initial_solution) < self.n:
                initial_solution.append((0, 0))

        seed = []
        for day, period in initial_solution:
            seed.extend([day or 0, period or 0])

        pop = self.toolbox.population(n=self.population_size - 1)
        pop.append(creator.Individual(seed))

        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", lambda x: sum(f[0] for f in x) / len(x) if x else 0)
        stats.register("min", min)

        try:
            pop, _ = algorithms.eaSimple(
                pop,
                self.toolbox,
                cxpb=0.5,
                mutpb=0.2,
                ngen=self.generations,
                stats=stats,
                halloffame=hof,
                verbose=False,
            )
        except Exception as e:
            logger.error(f"Genetic algorithm failed: {e}")
            return None

        best = hof[0]
        return [(best[i * 2], best[i * 2 + 1]) for i in range(self.n)]
