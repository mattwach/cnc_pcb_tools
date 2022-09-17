# Note: this file is only for running tests.  No make is needed to use the software

PYTHON_FILES=$(foreach f,$(wildcard *.py),$f.force)
CHECK_PCB_CU_FILES=$(foreach f,$(wildcard tests/check_pcb_cu/*.nc),$f.force)
CHECK_PCB_EDGE_FILES=$(foreach f,$(wildcard tests/check_pcb_edge/*.nc),$f.force)
CHECK_PCB_DRILL_FILES=$(foreach f,$(wildcard tests/check_pcb_drill/*.nc),$f.force)

test: lint check

lint: $(PYTHON_FILES)
check: check_pcb_cu check_pcb_edge check_pcb_drill
check_pcb_cu: $(CHECK_PCB_CU_FILES)
check_pcb_drill: $(CHECK_PCB_DRILL_FILES)
check_pcb_edge: $(CHECK_PCB_EDGE_FILES)

$(PYTHON_FILES): %.force:
		pylint $(subst .force,,$@)

$(CHECK_PCB_CU_FILES): %.force:
		python3 check_pcb_cu.py $(subst .force,,$@)

$(CHECK_PCB_DRILL_FILES): %.force:
		python3 check_pcb_drill.py $(subst .force,,$@)

$(CHECK_PCB_EDGE_FILES): %.force:
		python3 check_pcb_edge.py $(subst .force,,$@)
