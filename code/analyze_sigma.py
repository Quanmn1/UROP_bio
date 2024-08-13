import numpy as np
from scipy import optimize, stats, signal
import matplotlib
from matplotlib import pyplot as plt
import os
import sys
from helper import *

matplotlib.rcParams.update({'font.size': 14})

def analyze_sigma(test_name, mode, vars, num_segments, walls=False):
    # input: sequence of rhos.
    # output: plot sigma(rho)
    number = len(vars)
    rhos = vars
    if mode == "pfap":
        file = test_name + f'_{rhos[0]}'
        params, N = read_param(file + '_param')
        box_size = np.ceil(params['r_max_pfap'])
    else:
        file = test_name + f'_{rhos[0]:.0f}'
        params, N = read_param(file + '_param')
        box_size = params['r_max_qsap']

    density_box_size = params['density_box_size']
    Lx = params['Lx']
    

    # if walls, only average in the bulk (80 to 120, say)
    if walls:
        bulk_left = int(Lx*3/10 / box_size)
        bulk_right = int(Lx*7/10 / box_size)
    else:
        bulk_left = 0
        bulk_right = int(Lx / box_size)

    # Average over EVERY SNAPSHOTS
    sigmas = np.zeros((number, num_segments))
    rhos_bulk = np.zeros((number, num_segments))
    lefts = np.zeros((number, num_segments))
    rights = np.zeros((number, num_segments))
    # lefts = np.zeros(number)
    # rights = np.zeros(number)
    stds = np.zeros((number, num_segments))
    std_rhos = np.zeros((number, num_segments))
    for (ind,rho) in enumerate(rhos):
        if mode == "pfap":
            file = test_name + f'_{rho}'
        else:
            file = test_name + f'_{rho:.0f}'
        
        if not walls:
            sigmafile = file + '_sigma_data'
        else:
            sigmafile = file + '_sigmaIK/' + file + '_sigmaIK_xx_data'
        plot_name = 'direct_pressure'
        try:
            sigma=np.loadtxt(sigmafile)
        except OSError:
            print(f"No sigma file for {rho}")
            continue

        densityfile = file + '_density_data'
        try:
            density=np.loadtxt(densityfile)
        except OSError:
            print(f"No density file for {rho}")
            continue

        L = sigma.shape[0]
        N = density.shape[0]
        for i in range(num_segments):
            sigma_i = sigma[L*i//num_segments:L*(i+1)//num_segments, bulk_left:bulk_right]
            density_i = density[N*i//num_segments:N*(i+1)//num_segments, bulk_left//density_box_size:bulk_right//density_box_size]

            sigmas[ind, i] = np.mean(sigma_i)
            rhos_bulk[ind, i] = np.mean(density_i)
            # std over spatial and temporal fluctuations. 
            # doesn't mean anything for pressures, since value in each cell depends on whether there is a particle in that cell or not.
            std_rhos[ind, i] = np.std(density_i)/np.sqrt(N//num_segments)
            stds[ind, i] = np.std(sigma_i)/np.sqrt(L//num_segments)
        
        if walls:
            wallfile = file + "_wall_pressure"
            wall_pressure = np.loadtxt(wallfile)
            left_wall = wall_pressure[:,1]
            right_wall = wall_pressure[:,2]
            M = len(left_wall)
            for i in range(num_segments):
                left_i = left_wall[M*i//num_segments:M*(i+1)//num_segments]
                right_i = right_wall[M*i//num_segments:M*(i+1)//num_segments]
                lefts[ind, i] = np.mean(left_i)
                rights[ind, i] = np.mean(right_i)
            # lefts[ind] = np.mean(left_wall[M//num_segments:])
            # std_left[ind] = np.std(left_wall[M//num_segments:])
            # rights[ind] = np.mean(right_wall[M//num_segments:])
            # std_right[ind] = np.std(right_wall[M//num_segments:])

        # N = data.size
        # # obtain sigma average
        # sigmas[ind] = np.average(data)
        # sigma_stds[ind] = np.std(data)/np.sqrt(N)

    # plot sigma vs rho
    fig, ax = plt.subplots()
    ax.set_xlabel(r'$\rho$')
    ax.set_ylabel(r'$p(\rho)$')
    final_time = params["final_time"]
    start_time = params["next_store_time"]
    legends = [f"Time {(final_time-start_time)*i//num_segments+start_time}-{(final_time-start_time)*(i+1)//num_segments+start_time}" for i in range(num_segments)]

    """
    Fit functions
    """
    # if mode == "pfap":
    #     v = params['v']*np.exp(-0.4*np.tanh((0.78-25)/10))
    #     r_pf = params['r_max_pfap']
    #     rho_max = 2/np.sqrt(3)/r_pf/r_pf
    #     rho_dense = np.linspace(0,1.1,100)
    #     # v_expecteds = v*(1-rhos/rho_max)
    #     # ax.plot(rhos, v_expecteds, label=r"$v_0 (1-\rho / \rho_m)$")
    #     popt, pcov = optimize.curve_fit(linear, rhos, vs, p0=(-v/rho_max, v), sigma=v_stds, absolute_sigma=True)
    #     ax.plot(rho_dense, linear(rho_dense, *popt), label="Linear fit")
    #     perr = np.sqrt(np.diag(pcov))
    #     ax.text(0.6, 0.5, fr"$v = {popt[1]:.2f}\times (1 - \rho/{-popt[1]/popt[0]:.2f})$")
    # elif mode == "qsap":
    #     v = params['v']
    #     phi = params['phi']
    #     rho_m = params['rho_m']
    #     lamb = params['lambda']
    #     rho_dense = np.linspace(0, 60, 1000)
    #     v_expecteds = v*np.exp(-lamb*np.tanh((rho_dense-rho_m)/phi))
    #     ax.plot(rho_dense, v_expecteds, label='Expected veff')           
    # elif mode == "pfqs":
    #     v = params['v']
    #     phi = params['phi']
    #     rho_m = params['rho_m']
    #     lamb = params['lambda']
    #     r_pf = params['r_max_pfap']
    #     rho_dense = np.linspace(0, 60, 1000)
    #     v_expecteds = v*np.exp(-lamb*np.tanh((rho_dense-rho_m)/phi))*(1-rho_dense/(1.29/r_pf**2))
    #     ax.plot(rho_dense, v_expecteds, label=r'$v(\rho)(1-\rho r_f^2/1.29)$')     
    
    """
    Checking whether the system has equilibriated at the beginning of the recorded data
    """
    for i in range(num_segments):
        ax.errorbar(rhos_bulk[:,i], sigmas[:,i], ls='', marker='.')
    
    """
    After ascertaining that it has equilibriated:
    Plot averages and stds. Each segment is only one snapshot. 
    equi_index is the snapshot index at which we assume equilibrium has been reached (say, t=200)
    """
    if not walls:
        equi_index = 0 # since (we can verify that) data starts at equilibrium (e.g. t=100)
        plot_name = 'sigma_convergence'
    else:
        equi_index = 20 # since data starts at t=0.
        plot_name = 'bulk_vs_wall'
    num_snapshots = num_segments - equi_index
    std_density = np.std(rhos_bulk[:,equi_index:], axis=-1)/np.sqrt(num_snapshots)
    std_sigma = np.std(sigmas[:,equi_index:], axis=-1)/np.sqrt(num_snapshots)
    rho_bulk = np.mean(rhos_bulk[:,equi_index:], axis=-1)
    sigmas_avg = np.mean(sigmas[:,equi_index:], axis=-1)
    ax.errorbar(rho_bulk, sigmas_avg, xerr=std_density, yerr=std_sigma, ls='', marker='.', ms=4, label="Bulk pressure")
    
    if walls:
        std_left= np.std(lefts[:,equi_index:], axis=-1)/np.sqrt(num_snapshots)
        std_right = np.std(rights[:,equi_index:], axis=-1)/np.sqrt(num_snapshots)
        lefts_avg = np.mean(lefts[:,equi_index:], axis=-1)
        rights_avg = np.mean(rights[:,equi_index:], axis=-1)
        ax.errorbar(rho_bulk, lefts_avg, xerr=std_density, yerr=5*std_left, ls='', marker='.', ms=4, label="Left wall pressure")
        ax.errorbar(rho_bulk, rights_avg, xerr=std_density, yerr=5*std_right, ls='', marker='.', ms=4, label="Right wall pressure")
    
    ax.legend(legends)
    ax.set_xlim(left=0)
    # ax.set_ylim(bottom=0)
    ax.set_title("Total pressures")
    plt.savefig(f'{test_name}_{plot_name}.png',  dpi=500, bbox_inches='tight')

    if walls:
        output = test_name + '_total_pressure'
        with open(output, 'w') as f:
            f.write(f"rho \t \t rho_std \t bulk \t bulk_std \t left_wall \t left_std \t right_wall \t right_std\n")
            for i in range(len(rhos)):
                f.write(f"{rho_bulk[i]:.4f}\t{std_density[i]:.4f}\t{sigmas_avg[i]:.4f}\t{std_density[i]:.4f}\t{lefts_avg[i]:.4f}\t{std_left[i]:.4f}\t{rights_avg[i]:.4f}\t{std_right[i]:.4f}\n")
    else:
        output = test_name + '_sigma_data'
        with open(output, 'w') as f:
            f.write(f"rho \t \t rho_std \t bulk \t bulk_std\n")
            for i in range(len(rhos)):
                f.write(f"{rho_bulk[i]:.4f}\t{std_density[i]:.4f}\t{sigmas_avg[i]:.4f}\t{std_density[i]:.4f}\n")

if __name__ == "__main__":
    test_name = sys.argv[1]
    mode = sys.argv[2]
    # start = float(sys.argv[3])
    # end = float(sys.argv[4])
    # space = float(sys.argv[5])
    vars = np.array(sys.argv[3].split(),dtype=float)
    # vars = sys.argv[3].split()
    num_segments = int(sys.argv[4])
    if len(sys.argv) >= 6:
        walls = bool(sys.argv[5])
    else:
        walls = False

    analyze_sigma(test_name, mode, vars, num_segments, walls=walls)