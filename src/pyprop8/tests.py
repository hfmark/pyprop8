import numpy as np
import pyprop8 as pp
from pyprop8.utils import stf_trapezoidal,rtf2xyz,make_moment_tensor
from collections import defaultdict

def test_spatial_derivatives(model,source,stations,nt=257,dt=0.5,alpha = 0.023,
                             pad_frac = 1,derivatives=None,
                             delta = 1e-4,delta_scales={'depth':1,'phi':1e-2,'r':1},
                             source_time_function=None):
    '''
    Compute finite-difference derivatives and compare with the 'analytic'
    derivatives generated by pyprop8. All arguments are as required by
    `pyprop8.compute_seismograms()` except:

    delta        - float, perturbation for finite-difference calculation
    delta_scales - dict, containing keys that correspond to the keywords
                   available when creating a `pyprop8.DerivativeSwitches()`
                   object, defining a parameter-specific rescaling for `delta`
                   to account for the fact that parameters are specified in
                   dimensionalised units. If key is not found, 'delta' is used
                   unmodified.


    '''
    print("Testing spatial derivatives against finite difference calculation...")
    if source.nsources>1: raise ValueError("test_derivatives requires a single force/mechanism")
    if source_time_function is None:
        source_time_function = lambda w:stf_trapezoidal(w,3,6)
    if derivatives is None:
        derivatives = pp.DerivativeSwitches(r=True,phi=True,depth=True)
    if type(delta_scales) is not defaultdict:
        # Make delta_scales have a default value of '1'
        delta_scales = defaultdict(lambda:1,**delta_scales)

    nDimSta = stations.nDim
    if derivatives.nderivs==0:
        raise ValueError("All derivatives are 'switched off'!")
    elif derivatives.nderivs>1:
        nDimDerivs = 1
    else:
        nDimDerivs = 0
    nDimChannels = 1
    if nt>1:
        nDimTime = 1
    else:
        nDimTime = 0

    # Function to handle slicing of derivative arrays regardless of shapes
    deriv_comp = lambda sl: tuple(nDimSta*[slice(None)]+nDimDerivs*[sl]+nDimChannels*[slice(None)]+nDimTime*[slice(None)])


    tt,seis0,drv = pp.compute_seismograms(model,source,stations,nt,dt,alpha,pad_frac = pad_frac,derivatives=derivatives,source_time_function=source_time_function)
    assert len(seis0.shape)==nDimSta+nDimChannels+nDimTime
    assert len(drv.shape) == nDimSta+nDimChannels+nDimTime+nDimDerivs
    drverrs = []

    if derivatives.r:
        sta_pert = stations.copy()
        sta_pert.rmin+=delta*delta_scales['r']
        sta_pert.rmax+=delta*delta_scales['r']
        tt,seis = pp.compute_seismograms(model,source,sta_pert,nt,dt,alpha,pad_frac = pad_frac,derivatives=None,source_time_function=source_time_function)
        fd = (seis - seis0)/(delta*delta_scales['r'])
        err = drv[deriv_comp(derivatives.i_r)]-fd
        if nDimTime == 0:
            norm = abs(drv[deriv_comp(derivatives.i_r)])
        else:
            norm = abs(drv[deriv_comp(derivatives.i_r)]).max(-1)
        maxerr = (abs(err)/norm.reshape(*norm.shape,1)).max()
        drverrs+=[maxerr]
        print("Max error, 'r' derivative:   %f%%"%(100*maxerr))
    if derivatives.phi:
        sta_pert = stations.copy()
        sta_pert.phimin+=delta*delta_scales['phi']
        sta_pert.phimax+=delta*delta_scales['phi']
        tt,seis = pp.compute_seismograms(model,source,sta_pert,nt,dt,alpha,pad_frac = pad_frac,derivatives=None,source_time_function=source_time_function)
        fd = (seis - seis0)/(delta*delta_scales['phi'])
        err = drv[deriv_comp(derivatives.i_phi)]-fd
        if nDimTime == 0:
            norm = abs(drv[deriv_comp(derivatives.i_phi)])
        else:
            norm = abs(drv[deriv_comp(derivatives.i_phi)]).max(-1)
        maxerr = (abs(err)/norm.reshape(*norm.shape,1)).max()
        drverrs+=[maxerr]
        print("Max error, 'phi' derivative: %f%%"%(100*maxerr))
    if derivatives.depth:
        source_pert = source.copy()
        source_pert.dep-=delta*delta_scales['depth']
        tt,seis = pp.compute_seismograms(model,source_pert,stations,nt,dt,alpha,pad_frac = pad_frac,derivatives=None,source_time_function=source_time_function)
        fd = (seis - seis0)/delta
        err = drv[deriv_comp(derivatives.i_dep)]-fd
        if nDimTime == 0:
            norm = abs(drv[deriv_comp(derivatives.i_dep)])
        else:
            norm = abs(drv[deriv_comp(derivatives.i_dep)]).max(-1)
        maxerr = (abs(err)/norm.reshape(*norm.shape,1)).max()
        drverrs+=[maxerr]
        print("Max error, 'depth' derivative: %f%%"%(100*maxerr))
    return drverrs
if __name__=='__main__':
    stations = pp.RegularlyDistributedReceivers(10,150,5,0,360,8,depth=5)
    model = pp.LayeredStructureModel([(3.,1.8,0.,1.02),(2.,4.5,2.4,2.57),(5.,5.8,3.3,2.63),(20.,6.5,3.65,2.85),(np.inf,8.,4.56,3.34)])
    source = pp.PointSource(0,0,20,rtf2xyz(make_moment_tensor(340,90,0,2.4E8,0,0)),np.zeros([3,1]),0)
    errs = test_spatial_derivatives(model,source,stations)
    if max(errs)>1e-4:
        print("")
        print("*** Warning: Mismatch between analytic and finite-difference derivatives? ***")
        print("")
    else:
        print("Analytic derivatives agree with finite-difference approximation")
