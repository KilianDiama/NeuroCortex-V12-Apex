import asyncio
import logging
import os
import signal
from dataclasses import dataclass
from decimal import Decimal, getcontext
from enum import Enum
from typing import Dict, Final, List, Optional
import ujson as json
import aiofiles

# Précision chirurgicale pour la simulation neuro-chimique
getcontext().prec = 32

# ==============================
# DOMAIN: ARCHITECTURE DES ÉTATS
# ==============================

class MindState(Enum):
    ZENITH  = (Decimal("85"), "💎", "Clarté totale, optimisation neuronale.")
    FLOW    = (Decimal("65"), "🌊", "Concentration fluide, résilience haute.")
    STABLE  = (Decimal("45"), "⚖️", "Équilibre homéostatique, repos suggéré.")
    FRAGILE = (Decimal("20"), "🥀", "Vigile système, réduction des stimuli.")
    BURNOUT = (Decimal("0"),  "🌋", "Dépassement allostatique, arrêt d'urgence.")

    def __init__(self, threshold: Decimal, icon: str, desc: str):
        self.threshold = threshold
        self.icon = icon
        self.desc = desc

    @classmethod
    def from_energy(cls, energy: Decimal) -> 'MindState':
        for state in sorted(cls, key=lambda x: x.threshold, reverse=True):
            if energy >= state.threshold:
                return state
        return cls.BURNOUT

@dataclass(frozen=True)
class NeuroConfig:
    MAX_RESERVE: Final[Decimal] = Decimal("100.0")
    ALLOSTATIC_LIMIT: Final[Decimal] = Decimal("60.0")
    RECOVERY_BIAS: Final[Decimal] = Decimal("0.025")
    EQUILIBRIUM: Final[Decimal] = Decimal("75.0")
    PLASTICITY_COEFF: Final[Decimal] = Decimal("0.08")

# ==============================
# ENGINE: MOTEUR NEURO-DYNAMIQUE
# ==============================

class NeuroEngine:
    """Simulateur de thermodynamique cognitive avec gestion de l'usure."""
    __slots__ = ('config', 'allostatic_load')
    
    def __init__(self, config: NeuroConfig):
        self.config = config
        self.allostatic_load = Decimal("0")

    def calculate_impact(self, intensity: Decimal, weight: Decimal) -> Decimal:
        impact = intensity * weight
        
        # Mise à jour de la charge (Loi de l'usure cumulative)
        if impact < 0:
            self.allostatic_load += abs(impact) * Decimal("0.35")
        else:
            # La récupération est plus lente que l'usure
            recovery_factor = Decimal("0.12")
            self.allostatic_load = max(Decimal("0"), self.allostatic_load - (impact * recovery_factor))
        
        # Pénalité de fatigue (Croissance exponentielle de l'effort ressenti)
        fatigue_penalty = (self.allostatic_load / Decimal("10")) ** Decimal("1.18")
        return impact - fatigue_penalty

# ==============================
# CORE: NEUROCORTEX V12 APEX
# ==============================

class NeuroCortexV12:
    def __init__(self, user_name: str):
        self.user_name: Final = user_name
        self.config = NeuroConfig()
        self.engine = NeuroEngine(self.config)
        self._energy = self.config.EQUILIBRIUM
        self.synaptic_weights: Dict[str, Decimal] = {}
        self._lock = asyncio.Lock()
        self.storage_file = f"cortex_{self.user_name.lower()}.json"
        self.logger = self._init_logger()

    def _init_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"Neuro.{self.user_name}")
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("\033[94m%(asctime)s\033[0m | %(message)s", "%H:%M:%S"))
            logger.addHandler(h)
        return logger

    async def boot(self):
        """Initialisation sécurisée du Nexus."""
        if os.path.exists(self.storage_file):
            try:
                async with aiofiles.open(self.storage_file, "r") as f:
                    data = json.loads(await f.read())
                    self._energy = Decimal(data["energy"])
                    self.engine.allostatic_load = Decimal(data["allostatic_load"])
                    self.synaptic_weights = {k: Decimal(v) for k, v in data["weights"].items()}
                self.logger.info(f"✨ Nexus opérationnel pour \033[1m{self.user_name}\033[0m.")
            except Exception as e:
                self.logger.error(f"❌ Erreur de chargement : {e}")

    async def process_stimulus(self, tag: str, intensity: Decimal):
        """Cycle de traitement temps réel."""
        async with self._lock:
            weight = self.synaptic_weights.get(tag, Decimal("1.0"))
            
            # 1. Calcul de la variation nette
            net_change = self.engine.calculate_impact(intensity, weight)
            
            # 2. Mise à jour de l'énergie avec rappel homéostatique
            self._energy = (self._energy + net_change).max(Decimal("0")).min(self.config.MAX_RESERVE)
            
            # Force de rappel vers l'équilibre (Résilience naturelle)
            homoeostatic_push = (self.config.EQUILIBRIUM - self._energy) * self.config.RECOVERY_BIAS
            self._energy += homoeostatic_push
            
            # 3. Neuroplasticité : Adaptation dynamique des poids
            if net_change < 0:
                # Sensibilisation aux facteurs de stress
                self.synaptic_weights[tag] = min(Decimal("4.0"), weight + self.config.PLASTICITY_COEFF)
            else:
                # Accoutumance aux stimuli positifs (Hédonisme adaptatif)
                self.synaptic_weights[tag] = max(Decimal("0.3"), weight - (self.config.PLASTICITY_COEFF / 2))

            self._render_ui(tag, net_change)
            await self._save_atomic()

    def _render_ui(self, tag: str, delta: Decimal):
        state = MindState.from_energy(self._energy)
        load_pct = (self.engine.allostatic_load / self.config.ALLOSTATIC_LIMIT) * 100
        color = "\033[92m" if delta > 0 else "\033[91m"
        
        status_line = (
            f"{state.icon} [\033[1m{self._energy:>5.2f}%\033[0m] | "
            f"{tag:<15} | Δ: {color}{delta:>+6.2f}\033[0m | "
            f"Charge: {load_pct:>5.1f}%"
        )
        self.logger.info(status_line)

    async def _save_atomic(self):
        """Sauvegarde sécurisée pour éviter toute perte de données."""
        temp_file = f"{self.storage_file}.tmp"
        payload = {
            "energy": str(self._energy),
            "allostatic_load": str(self.engine.allostatic_load),
            "weights": {k: str(v) for k, v in self.synaptic_weights.items()}
        }
        async with aiofiles.open(temp_file, "w") as f:
            await f.write(json.dumps(payload, indent=4))
        os.replace(temp_file, self.storage_file)

# ==============================
# EXECUTION: TEST DE PERFORMANCE
# ==============================

async def run_simulation():
    cortex = NeuroCortexV12("Kiliandiama")
    await cortex.boot()

    events = [
        ("Sommeil Réparateur", Decimal("30")),
        ("Focus Profond", Decimal("-12")),
        ("Session Sport", Decimal("15")),
        ("Stress Bureau", Decimal("-25")),
        ("Méditation", Decimal("10")),
    ]

    print(f"\n\033[1m--- DÉMARRAGE DU SYSTÈME NEUROCORTEX V12 ---\033[0m")
    
    for cycle in range(1, 3):
        print(f"\n[CYCLE DE STABILISATION {cycle}]")
        for tag, val in events:
            await cortex.process_stimulus(tag, val)
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        pass
    print(f"\n\033[1m--- SYSTÈME REBOOTÉ. ÉTAT SAUVEGARDÉ. ---\033[0m")
