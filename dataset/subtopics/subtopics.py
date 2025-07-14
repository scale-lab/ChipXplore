from config.sky130 import View
from dataset.subtopics.lib_subtopics import LIB_SUBTOPICS 
from dataset.subtopics.lef_subtopics import LEF_SUBTOPICS 
from dataset.subtopics.tlef_subtopics import TECHLEF_SUBTOPICS


SUBTOPICS_BYVIEW = {
    View.Lef.value: LEF_SUBTOPICS,
    View.TechLef.value: TECHLEF_SUBTOPICS,
    View.Liberty.value: LIB_SUBTOPICS
}
