# Makefile to create the bar- and mixing cards.                      \
                                                                     \
Usage is described in BRUGSANVISNING.txt (in Danish)

# Use Python 3 it it exists, else use Python 2.
ifeq ($(shell which python3),)
  PYTHON = python
else
  PYTHON = python3
endif

#####################
# Generating output #
#####################
# Defaults
fest ?= drinks
sort ?= sorted
alt  ?= nej
columns ?= new

ifeq ($(alt),nej)
    alt_arg :=
else
    alt_arg := -a
endif

ifeq ($(sort),sorted)
    sort_arg := -s
else
    sort_arg :=
endif

# Run it all!
default: clean-deep all

all: bar_$(fest).pdf mixing_$(fest).pdf


# Create the barcards
bar_$(fest).pdf: barcard.tex barcardmain.tex
	xetex -jobname=bar_$(fest) -output-driver="xdvipdfmx -q -E -p a4 -l" barcardmain.tex

# Create the mixing card
mixing_$(fest).pdf: mixing.tex mixingcardmain.tex
	pdflatex -jobname=mixing_$(fest) mixingcardmain.tex

# Generate the tables using python magic!
barcard.tex: drinks.py $(fest).txt
	$(PYTHON) $< $(sort_arg) $(alt_arg) -c $(columns) $(fest).txt


###########
# Testing #
###########

# See if there is any errors in the provided input file...
test: drinks.py $(fest).txt
	$(PYTHON) $< -v $(fest).txt



################
# Housekeeping #
################

clean: clean-junk clean-tex

clean-deep: clean clean-out

clean-junk:
	$(RM) *.log *.aux

clean-tex:
	$(RM) mixing.tex barcard.tex

clean-out:
	$(RM) *.pdf
