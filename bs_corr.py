import numpy as np
from pybaselines import Baseline





def correct_baseline(intensity: np.ndarray, method: str = 'derpsalsa', **kwargs) -> tuple[np.ndarray, dict]:
    """
    Apply baseline correction to a spectrum.
    
    Args:
        intensity: Array of intensity values
        method: Baseline correction method. Options:
            'derpsalsa' - Derivative Peak-Screening Asymmetric Least Squares (default)
            'asls' - Asymmetric Least Squares
            'arpls' - Asymmetric Reweighted Penalized Least Squares
            'mor' - Morphological baseline
            'snip' - Statistics-sensitive Non-linear Iterative Peak-clipping
        **kwargs: Additional parameters for the specific method
            For 'derpsalsa': lam (smoothness), p (asymmetry), default: lam=10**5.5, p=0.001
            For 'asls': lam, p, default: lam=10**6, p=0.01
            For 'arpls': lam, default: lam=10**5
            For 'mor': half_window, default: half_window=30
            For 'snip': max_half_window, default: max_half_window=40
    
    Returns:
        corrected_intensity: Baseline-corrected intensity
        params: Dictionary with baseline and other parameters returned by the method
    """
    # Initialize pybaselines object for baseline correction
    _baseline_fitter = Baseline()
    if method == 'derpsalsa':
        lam = kwargs.get('lam', 10**5.5)
        p = kwargs.get('p', 0.001)
        baseline, params = _baseline_fitter.derpsalsa(intensity, lam=lam, p=p)
    elif method == 'asls':
        lam = kwargs.get('lam', 10**6)
        p = kwargs.get('p', 0.01)
        baseline, params = _baseline_fitter.asls(intensity, lam=lam, p=p)
    elif method == 'arpls':
        lam = kwargs.get('lam', 10**5)
        baseline, params = _baseline_fitter.arpls(intensity, lam=lam)
    elif method == 'mor':
        half_window = kwargs.get('half_window', 30)
        baseline, params = _baseline_fitter.mor(intensity, half_window=half_window)
    elif method == 'mormol':
        half_window = kwargs.get('half_window', 30)
        baseline, params = _baseline_fitter.mormol(intensity, half_window=half_window)
    elif method == 'snip':
        max_half_window = kwargs.get('max_half_window', 40)
        baseline, params = _baseline_fitter.snip(intensity, max_half_window=max_half_window)
    elif method == 'poly':
        degree = kwargs.get('degree', 1)
        baseline, params = _baseline_fitter.poly(intensity, poly_order=degree)
    elif method == 'manual_poly':
        degree = kwargs.get('degree', 1)
        intensity_initial = intensity[5:27]
        intensity_final = intensity[-22:]
        intensity = np.concatenate([intensity_initial, intensity_final])
        baseline, params = _baseline_fitter.poly(intensity, poly_order=degree)
    else:
        raise ValueError(f"Unknown baseline correction method: {method}")
    
    corrected_intensity = intensity - baseline
    params['baseline'] = baseline
    
    return corrected_intensity, params
