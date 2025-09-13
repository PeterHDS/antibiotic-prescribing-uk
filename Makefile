.PHONY: all data clean analyze figures

all: data clean analyze figures

data:
	python src/get_data.py

clean:
	python src/clean.py

analyze:
	python src/analyze.py

figures:
	python src/charts.py
