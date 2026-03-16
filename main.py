from fitting import fit_currents
from plot_fit_params import plot_fit_params
from read_excel import read_excel

if __name__ == "__main__":
    #read_excel()
    fit_results = fit_currents(bs_method='integrated')
    plot_fit_params()