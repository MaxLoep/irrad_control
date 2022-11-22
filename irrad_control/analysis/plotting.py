from cProfile import label
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md
from irrad_control.analysis import formulas as fm
import irrad_control.analysis.constants as irrad_consts

from datetime import datetime
from matplotlib.colors import LogNorm
from pkg_resources import VersionConflict

from irrad_control.analysis.formulas import lin_odr


def _get_damage_label_unit_target(damage, dut=False):
    damage_unit = r'n$_\mathrm{eq}$ cm$^{-2}$' if damage == 'neq' else r'p cm$^{-2}$' if damage == 'proton' else 'Mrad'
    damage_label = 'Fluence' if damage in ('neq', 'proton') else 'Total Ionizing Dose'
    damage_target = "DUT" if dut else "Scan"
    return damage_label, damage_unit, damage_target

def _apply_labels_damage_plots(ax, damage, server, cbar=None, dut=False, damage_map=None, uncertainty_map=False):

    damage_label, damage_unit, damage_target = _get_damage_label_unit_target(damage=damage, dut=dut)

    ax.set_xlabel(f'{damage_target} area horizontal / mm')
    ax.set_ylabel(f'{damage_target} area vertical / mm')
    plt.suptitle(f"{damage_label}{' Error' if uncertainty_map else ''} Distribution {damage_target} Area (Server: {server})")

    # 3D plot
    if hasattr(ax, 'set_zlabel'):
        ax.set_zlabel(f"{damage_label} / {damage_unit}")

    if damage_map is not None and dut and not uncertainty_map:
        mean, std = damage_map.mean(), damage_map.std()
        damage_mean_std = "Mean = {:.2E}{}{:.2E} {}".format(mean, u'\u00b1', std, damage_unit)
        ax.set_title(damage_mean_std)

    if cbar is not None:
        cbar_label = f"{damage_label} / {damage_unit}"
        cbar.set_label(cbar_label)

def _make_cbar(fig, damage_map, damage, rel_error_lims=None):

    damage_label, damage_unit, _ = _get_damage_label_unit_target(damage=damage, dut=False)

    # Make axis for cbar
    cbar_axis = plt.axes([0.85, 0.1, 0.033, 0.8])
    cbar = fig.colorbar(damage_map, cax=cbar_axis, label=f"{damage_label} / {damage_unit}")

    if rel_error_lims is not None:
        cbar_rel_axis = cbar_axis.twinx()
        cbar.ax.yaxis.set_ticks_position('left')
        cbar.ax.yaxis.set_label_position('left')
        cbar_rel_axis.set_ylabel("Relative uncertainty / %")
        cbar_rel_axis.ticklabel_format(axis='y', useOffset=False, style='plain')
        cbar_rel_axis.set_ylim(rel_error_lims)


def plot_damage_error_3d(damage_map, error_map, map_centers_x, map_centers_y, view_angle=(25, -115), cmap='viridis', contour=False, **damage_label_kwargs):

    # Make figure
    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw={"projection": "3d"})

    # Generate meshgird to plot on
    mesh_x, mesh_y = np.meshgrid(map_centers_x, map_centers_y)

    # plot surface
    surface_3d = ax.plot_surface(mesh_x, mesh_y, error_map, antialiased=True, cmap=cmap)
    
    # Adjust angle
    ax.view_init(*view_angle)
    ax.set_ylim(ax.get_ylim()[::-1])  # Inverty y axis in order to set origin to upper left

    # Relative errors
    rel_damage_map = error_map / damage_map * 100.0

    _make_cbar(fig=fig, damage_map=surface_3d, damage=damage_label_kwargs.get('damage', 'neq'), rel_error_lims=(rel_damage_map.min(), rel_damage_map.max()))

    # Apply labels
    _apply_labels_damage_plots(ax=ax, damage_map=damage_map, uncertainty_map=True, **damage_label_kwargs)

    return fig, ax



def plot_damage_map_3d(damage_map, map_centers_x, map_centers_y, view_angle=(25, -115), cmap='viridis', contour=False, **damage_label_kwargs):

    # Make figure
    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw={"projection": "3d"})

    # Generate meshgird to plot on
    mesh_x, mesh_y = np.meshgrid(map_centers_x, map_centers_y)

    # plot surface
    surface_3d = ax.plot_surface(mesh_x, mesh_y, damage_map, antialiased=True, cmap=cmap)

    # Plot contour
    if contour:
        contour_2d = ax.contourf(mesh_x, mesh_y, damage_map, zdir='z', offset=-0.05*damage_map.max(), cmap=cmap)
        ax.set_zlim(-0.05*damage_map.max(), damage_map.max())
        
    # Adjust angle
    ax.view_init(*view_angle)
    ax.set_ylim(ax.get_ylim()[::-1])  # Inverty y axis in order to set origin to upper left

    _make_cbar(fig=fig, damage_map=surface_3d, damage=damage_label_kwargs.get('damage', 'neq'))
    
    # Apply labels
    _apply_labels_damage_plots(ax=ax, damage_map=damage_map, **damage_label_kwargs)

    return fig, ax


def plot_damage_map_2d(damage_map, map_centers_x, map_centers_y, cmap='viridis', **damage_label_kwargs):

    # Make figure
    fig, ax = plt.subplots(figsize=(8, 6))
    
    bin_width_y = (map_centers_y[1] - map_centers_y[0])
    bin_width_x = (map_centers_x[1] - map_centers_x[0])
    
    extent = [map_centers_x[0] - bin_width_x/2., map_centers_x[-1] + bin_width_x/2., map_centers_y[-1] + bin_width_y/2., map_centers_y[0]- bin_width_y/2.]

    im = ax.imshow(damage_map, extent=extent, cmap=cmap)

    cbar = fig.colorbar(im)

    # Apply labels
    _apply_labels_damage_plots(ax=ax, cbar=cbar, damage_map=damage_map, **damage_label_kwargs)

    return fig, ax

def plot_damage_map_contourf(damage_map, map_centers_x, map_centers_y, cmap='viridis', **damage_label_kwargs):

    # Make figure
    fig, ax = plt.subplots(figsize=(8, 6))

     # Generate meshgird to plot on
    mesh_x, mesh_y = np.meshgrid(map_centers_x, map_centers_y)

    # Plot contour
    contour_2d = ax.contourf(mesh_x, mesh_y, damage_map, cmap=cmap)
    _ = plt.clabel(contour_2d, inline=True, fmt='%1.2E', colors='k')
    ax.set_ylim(ax.get_ylim()[::-1])  # Inverty y axis in order to set origin to upper left

    cbar = fig.colorbar(contour_2d)
    
    # Apply labels
    _apply_labels_damage_plots(ax=ax, cbar=cbar, damage_map=damage_map, **damage_label_kwargs)

    return fig, ax

def plot_generic_axis(axis_data, fig_ax=None, set_grid=True, **sp_kwargs):
    fig, ax = plt.subplots(**sp_kwargs) if fig_ax is None else fig_ax
    
    ax.set_title(axis_data['title'])
    ax.set_xlabel(axis_data['xlabel'])
    ax.set_ylabel(axis_data['ylabel'])
    if set_grid: ax.grid()
    return fig, ax
    

def plot_generic_fig(plot_data, fit_data=None, hist_data=None, fig_ax=None, **sp_kwargs):
    fig, ax = plt.subplots(**sp_kwargs) if fig_ax is None else fig_ax
    
    # Make figure and axis
    ax.set_title(plot_data['title'])
    ax.set_xlabel(plot_data['xlabel'])
    ax.set_ylabel(plot_data['ylabel'])
    
    if fit_data:
        ax.plot(fit_data['xdata'], fit_data['func'](*fit_data['fit_args']), fit_data['fmt'], label=fit_data['label'], zorder=10)
    if hist_data:
        if isinstance(hist_data['bins'], (int, str)):
            if hist_data['bins'] == 'stat':
                n, s = np.mean(plot_data['xdata']), np.std(plot_data['xdata'])
                binwidth = 6 * s / 100.
                bins = np.arange(n-3*s, n+3*s + binwidth, binwidth)
            else:
                bins = hist_data['bins']

            _, _, _ = ax.hist(plot_data['xdata'], bins=bins, label=plot_data['label'])
        elif len(hist_data['bins']) == 2:
            _, _, _, im = ax.hist2d(plot_data['xdata'], plot_data['ydata'], bins=hist_data['bins'],norm=hist_data['norm'], cmap=hist_data['cmap'], cmin=1)
            plt.colorbar(im)
        else:
            raise ValueError('bins must be 2D iterable of intsd or int')
    else:
        ax.plot(plot_data['xdata'], plot_data['ydata'], plot_data['fmt'], label=plot_data['label'])
    ax.grid()
    ax.legend(loc='upper left')
    
    return fig, ax



def plot_beam_current_over_time(timestamps, beam_current, ch_name):

    fig, ax = plot_generic_fig(plot_data={'xdata': [datetime.fromtimestamp(ts) for ts in timestamps],
                                          'ydata': beam_current,
                                          'xlabel': 'Time',
                                          'ylabel': f"Cup channel {ch_name} current / nA",
                                          'label': f'{ch_name} current',
                                          'title': f"Current of channel {ch_name}",
                                          'fmt': 'C0.'},
                               figsize=(8,6))

    ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M'))
    fig.autofmt_xdate()

    return fig, ax


def plot_calibration(calib_data, ref_data, calib_sig, ref_sig, red_chi, beta_lambda, hist=False):

    beta_const, lambda_const = beta_lambda

    fit_label=r'Linear fit: $\mathrm{I_{cup}(I_{sem_{sum}})=\beta \cdot I_{sem_{sum}}}$;'
    fit_label += '\n\t' + r'$\mathrm{\beta=\lambda \cdot 5\ V=(%.3f \pm %.3f)}$' % (beta_const.n, beta_const.s)
    fit_label += '\n\t' + r'$\lambda=(%.3f \pm %.3f) \ V^{-1}$' % (lambda_const.n, lambda_const.s)
    fit_label += '\n\t' + r'$\chi^2_{red}= %.2f\ $' % red_chi

    # Make figure and axis
    fig, ax = plot_generic_fig(plot_data={'xdata': calib_data,
                                          'ydata': ref_data,
                                          'xlabel': f"Calibration sem_sum-type channel '{calib_sig}' current / nA",
                                          'ylabel': f"Reference cup-type channel '{ref_sig}' current / nA",
                                          'label': 'Correlation',
                                          'title':"Beam current calibration",
                                          'fmt':'C0.'},
                               fit_data={'xdata': calib_data,
                                         'func': lin_odr,
                                         'fit_args': [[beta_const.n], calib_data],
                                         'fmt': 'C1-',
                                         'label': fit_label},
                               hist_data={'bins': (100, 100), 'cmap': 'viridis', 'norm': LogNorm()} if hist else {},
                               figsize=(8,6))

    # Make figure and axis
    _, _ = ax.set_ylim(0, np.max(ref_data) * (1.25))
    
    return fig, ax

#******** Scanplotting *******#
def fluence_row_hist(start, end, fluence):
    tss = datetime.fromtimestamp(start)
    tse = datetime.fromtimestamp(end)
    tdiff = tse-tss
    tdiff = tdiff.total_seconds()
    tdiffh = (tdiff-tdiff%3600)/3600
    tdiff = tdiff%3600
    tdiffm = (tdiff-tdiff%60)/60
    
    unit = r'$\mathrm{p}\ \mathrm{cm}^{-2}$'
    fig_label = "Mean beam current over {} hours, {} mins.:\n({:.1e}±{:.1e}) {}".format(int(tdiffh), int(tdiffm), np.mean(fluence), np.std(fluence), unit)
    xlabel = r'$\mathrm{Fluence}\ /\ \mathrm{p}\ \mathrm{cm}^{-2}$'
    fig_title = "Histogram Of Fluence Per Row"
    fig, ax = plot_generic_fig(plot_data={'xdata': fluence,
                                          'xlabel': xlabel,
                                          'ylabel': f"#",
                                          'label': fig_label,
                                          'title': fig_title,
                                          'fmt': 'C0'},
                               hist_data={'bins': 'stat'},
                               figsize=(8,6))
    return fig, ax

def plot_tid_per_row(data, **kwargs):
    fig, ax = plot_generic_axis(axis_data={'xlabel': f"Row",
                                          'ylabel': f"Accumulated TID / Mrad",
                                          'title': "Rowwise radiation damage"},
                                figsize=(8,6))
    ax.grid(False)
    rows = [row for row in range(len(data))]
    bar_heights = np.zeros(len(rows))
    datalen = len(data[0])
    for scan_j in range(0,1):
        color, label = ('C0', "Damage")
        ax.bar(x=rows, height=data[:,scan_j], bottom=bar_heights, color=color, edgecolor=(0,0,0), linewidth=0.01, label=label)
        bar_heights = bar_heights+data[:,scan_j]
    ax.legend()
    for scan_i in range(1,datalen):
        ax.bar(x=rows, height=data[:,scan_i], bottom=bar_heights, color="C0", edgecolor=(0,0,0), linewidth=0.01)
        bar_heights = bar_heights+data[:,scan_i]
    ax.set_xlim(left=rows[0]-1, right=rows[-1]+1)
    ax.set_ylim(ymax=ax.get_ylim()[1]*1.1)
    neqax = ax.twinx()
    neqlabel = str(r'Fluence / n$_\mathrm{eq}$ cm$^{-2}$')
    neqax.set_ylabel(neqlabel)
    neqax.grid(axis='y')
    neq_ylims = [lim*kwargs['hardness_factor']/(1e5 * irrad_consts.elementary_charge * kwargs['stopping_power']) for lim in ax.get_ylim()]
    neqax.set_ylim(ymin=neq_ylims[0], ymax=neq_ylims[1])
    return fig, ax

def plot_everything(data, **kwargs):
    fig = plt.figure(figsize=(6, 6))
    gs = fig.add_gridspec(2, 1, height_ratios=(5, 1))#,
                        #left=0.1, right=0.9, bottom=0.1, top=0.9,
                        #wspace=0.05, hspace=0.05)
    beamax = fig.add_subplot(gs[0, 0])
    fig_title = "Row- and scanwise radiation damage"
    fig.suptitle(fig_title)
    dtime_row_start = [datetime.fromtimestamp(ts) for ts in data['row_start']]
    dtime_row_stop = [datetime.fromtimestamp(ts) for ts in data['row_stop']]
    tss = datetime.fromtimestamp(data['row_start'][0])
    day = tss.strftime("%d")
    month = tss.strftime("%B")
    year = tss.strftime("%Y")
    xtimelabel = "Time on {} {} {}".format(day, month, year)
    beamax.plot(dtime_row_start, data['beam_current'], color="C1", label="Beam")
    beamax.set_ylabel(f"Beam current / nA")
    scanax = beamax.twiny()
    scanax.set_xlim(beamax.get_xlim())
    
    beamax.grid(False)
    beamax.set_zorder(3)
    beamax.set_facecolor('none')
    bymin, bymax = beamax.get_ylim()
    beamax.set_ylim(bymin, 1.05*bymax) #make some room for labels
    tidax = beamax.twinx()
    neqax = beamax.twinx()
    
    beamax.spines['right'].set_position(('outward', 0.0))
    beamax.yaxis.tick_right()
    beamax.yaxis.set_label_position("right")

    neqlabel = str(r'Fluence / n$_\mathrm{eq}$ cm$^{-2}$')
    neqax.set_ylabel(neqlabel)
    neqax.spines['left'].set_position(('outward', 0))
    neqax.spines['left'].set_visible(True)
    neqax.yaxis.set_label_position("left")
    neqax.yaxis.tick_left()
    
    tidax.spines['left'].set_position(('outward', 55))
    tidax.spines['left'].set_visible(True)
    tidax.yaxis.set_label_position("left")
    tidax.yaxis.tick_left()
    
    ruderzeit = [dtime_row_stop[i] - dtime_row_start[i] for i in range(len(dtime_row_start))]
    tidax.bar(x=dtime_row_start, height=data['row_tid'], width=ruderzeit, label="Damage", color='C0', align='edge') #add tid per scan
    tidax.set_ylabel("TID / Mrad")
    ymin, ymax = tidax.get_ylim()
    tidax.set_ylim(ymin, 1.1*ymax) #make some room for labels
    
    n_scan = len(data['scan_start'])
    tick_dist = n_scan/5
    beamaxlabel = ["Scan {}".format(i+1) for i in range(n_scan) if (i-19)%tick_dist==0]
    dtime_scan_start = [datetime.fromtimestamp(data['scan_start'][i]) for i in range(n_scan) if (i-19)%tick_dist==0]
    beamax.set_xticks(dtime_scan_start)
    beamax.set_xticklabels(beamaxlabel)
    scanax.xaxis.set_major_formatter(md.DateFormatter('%H:%M'))
    scanax.set_xlabel(xtimelabel)
    
    beamlossax = fig.add_subplot(gs[1, 0], sharex=beamax)
    beamlossax.plot(dtime_row_start, data['beam_loss'], label="Beam loss", color="C2")
    beamlossax.legend()
    beamlossax.set_ylabel(f"Current loss / nA")
    beamlossax.spines['left'].set_visible(True)
    beamlossax.spines['right'].set_position(('outward', 0.0))
    beamlossax.yaxis.tick_right()
    beamlossax.yaxis.set_label_position("right")
    beamlossax.spines['right'].set_visible(True)
    #beamlossax.xaxis.set_major_formatter(md.DateFormatter('%H:%M'))

    neq_ylims = [lim*kwargs['hardness_factor']/(1e5 * irrad_consts.elementary_charge * kwargs['stopping_power']) for lim in tidax.get_ylim()]
    neqax.set_ylim(ymin=neq_ylims[0], ymax=neq_ylims[1])
    beamax.legend(loc='upper right')
    tidax.legend(loc='upper left')
    neqax.grid(axis='y')
    beamax.grid(axis='x')
    beamlossax.grid()
    return fig
    
#******* Beamplotting ********#
def plot_beam_current(timestamps, beam_currents, while_scan=None):
    tss = datetime.fromtimestamp(timestamps[0])
    day = tss.strftime("%d")
    month = tss.strftime("%B")
    year = tss.strftime("%Y")
    fig_title = "Beam current over time" if while_scan is None else "Beam current over time during scan"
    fig_label = "Beam"
    xlabel = "Time on {} {} {}".format(day, month, year)
    fig, ax = plot_generic_fig(plot_data={'xdata': [datetime.fromtimestamp(ts) for ts in timestamps],
                                          'ydata': beam_currents,
                                          'xlabel': xlabel,
                                          'ylabel': f"Beam current / nA",
                                          'label': fig_label,
                                          'title': fig_title,
                                          'fmt': '-C0'},
                               figsize=(8,6))
    ax.xaxis.set_major_formatter(md.DateFormatter('%H:%M'))
    fig.autofmt_xdate()
    return fig, ax

def plot_beam_current_hist(beam_currents, start, end, while_scan=None):
    tss = datetime.fromtimestamp(start)
    tse = datetime.fromtimestamp(end)
    tdiff = tse-tss
    tdiff = tdiff.total_seconds()
    tdiffh = (tdiff-tdiff%3600)/3600
    tdiff = tdiff%3600
    tdiffm = (tdiff-tdiff%60)/60

    fig_label = "Mean beam current over {} hours, {} mins.:\n({:.0f}±{:.0f}) nA".format(int(tdiffh), int(tdiffm), np.mean(beam_currents), np.std(beam_currents))
    fig_title = "Beam-Current Distribution" if while_scan is None else "Beam-current distribution during scan"
    fig, ax = plot_generic_fig(plot_data={'xdata': beam_currents,
                                          'xlabel': f"Beam current / nA",
                                          'ylabel': f"#",
                                          'label': fig_label,
                                          'title': fig_title,
                                          'fmt': 'C0'},
                               hist_data={'bins': 'stat'},
                               figsize=(8,6))
    return fig, ax

def plot_beam_deviation(horizontal_deviation, vertical_deviation, while_scan=None):
    fig = plt.figure(figsize=(6, 6))
    gs = fig.add_gridspec(2, 2,  width_ratios=(4, 1), height_ratios=(1, 4),
                        left=0.1, right=0.9, bottom=0.1, top=0.9,
                        wspace=0.05, hspace=0.05)
    ax = fig.add_subplot(gs[1, 0])
    ax_histx = fig.add_subplot(gs[0, 0], sharex=ax)
    ax_histy = fig.add_subplot(gs[1, 1], sharey=ax)
    ax_histy.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
    ax.grid()
    ax_histx.grid()
    ax_histy.grid()
    fig_title = "Relative beam-distribution from mean position" if while_scan is None \
        else "Relative beam-distribution from mean position while scanning"
    fig.suptitle(fig_title)
    ax.set_xlabel("x-deviation to left (-) and right (+) / % ")
    ax.set_ylabel("y-deviation upwards (+) and downwards (-) / %")
    n_bins = 100 #bins of 2% each
    _, _, _, im = ax.hist2d(horizontal_deviation, vertical_deviation, bins=(n_bins, n_bins),norm=LogNorm(), cmap='viridis', cmin=1)
    plt.colorbar(mappable=im, ax=ax_histy)
    xmean = np.mean(vertical_deviation)
    xstd = np.std(vertical_deviation)
    ymean = np.mean(horizontal_deviation)
    ystd = np.std(horizontal_deviation)
    xlabel = "({:.2f}±{:.2f}) %".format(xmean, xstd)
    ylabel = "({:.2f}±{:.2f}) %".format(ymean, ystd)
    _, _, _ = ax_histx.hist(vertical_deviation, bins=n_bins, label=xlabel)
    _, _, _ = ax_histy.hist(horizontal_deviation, bins=n_bins, orientation='horizontal', label=ylabel)
    ax_histx.legend()
    ax_histy.legend()
    ax_histx.tick_params(axis="x", labelbottom=False)
    ax_histy.tick_params(axis="y", labelleft=False)
    
    return fig, ax
