"""Ensemble predictors combining a sampler and a classifier."""

# Authors: Guillaume Lemaitre <g.lemaitre58@gmail.com>
#          Christos Aridas
# License: MIT

import numbers

import numpy as np

from sklearn.base import clone
from sklearn.ensemble import BaggingClassifier
from sklearn.tree import DecisionTreeClassifier

from ..pipeline import Pipeline
from ..under_sampling import RandomUnderSampler
from ..under_sampling.base import BaseUnderSampler
from ..utils import Substitution
from ..utils._docstring import _random_state_docstring


@Substitution(
    sampling_strategy=BaseUnderSampler._sampling_strategy_docstring,
    random_state=_random_state_docstring)
class BalancedBaggingClassifier(BaggingClassifier):
    """A Bagging classifier with additional balancing. It is similar to
    ``EasyEnsemble`` [6]_.

    This implementation of Bagging is similar to the scikit-learn
    implementation. It includes an additional step to balance the training set
    at fit time using a ``RandomUnderSampler``.

    Read more in the :ref:`User Guide <ensemble_meta_estimators>`.

    Parameters
    ----------
    base_estimator : object or None, optional (default=None)
        The base estimator to fit on random subsets of the dataset.
        If None, then the base estimator is a decision tree.

    n_estimators : int, optional (default=10)
        The number of base estimators in the ensemble.

    max_samples : int or float, optional (default=1.0)
        The number of samples to draw from X to train each base estimator.

        - If int, then draw ``max_samples`` samples.
        - If float, then draw ``max_samples * X.shape[0]`` samples.

    max_features : int or float, optional (default=1.0)
        The number of features to draw from X to train each base estimator.

        - If int, then draw ``max_features`` features.
        - If float, then draw ``max_features * X.shape[1]`` features.

    bootstrap : boolean, optional (default=True)
        Whether samples are drawn with replacement.

    bootstrap_features : boolean, optional (default=False)
        Whether features are drawn with replacement.

    oob_score : bool
        Whether to use out-of-bag samples to estimate
        the generalization error.

    warm_start : bool, optional (default=False)
        When set to True, reuse the solution of the previous call to fit
        and add more estimators to the ensemble, otherwise, just fit
        a whole new ensemble.

        .. versionadded:: 0.17
           *warm_start* constructor parameter.

    {sampling_strategy}

    replacement : bool, optional (default=False)
        Whether or not to sample randomly with replacement or not.

    n_jobs : int, optional (default=1)
        The number of jobs to run in parallel for both `fit` and `predict`.
        If -1, then the number of jobs is set to the number of cores.

    {random_state}

    verbose : int, optional (default=0)
        Controls the verbosity of the building process.

    ratio : str, dict, or callable
        .. deprecated:: 0.4
           Use the parameter ``sampling_strategy`` instead. It will be removed
           in 0.6.

    Attributes
    ----------
    base_estimator_ : estimator
        The base estimator from which the ensemble is grown.

    estimators_ : list of estimators
        The collection of fitted base estimators.

    estimators_samples_ : list of arrays
        The subset of drawn samples (i.e., the in-bag samples) for each base
        estimator. Each subset is defined by a boolean mask.

    estimators_features_ : list of arrays
        The subset of drawn features for each base estimator.

    classes_ : array, shape (n_classes,)
        The classes labels.

    n_classes_ : int or list
        The number of classes.

    oob_score_ : float
        Score of the training dataset obtained using an out-of-bag estimate.

    oob_decision_function_ : ndarray, shape (n_samples, n_classes)
        Decision function computed with out-of-bag estimate on the training
        set. If n_estimators is small it might be possible that a data point
        was never left out during the bootstrap. In this case,
        ``oob_decision_function_`` might contain NaN.

    Notes
    -----
    This is possible to turn this classifier into a balanced random forest [5]_
    by passing a :class:`sklearn.tree.DecisionTreeClassifier` with
    `max_features='auto'` as a base estimator.

    See
    :ref:`sphx_glr_auto_examples_ensemble_plot_comparison_bagging_classifier.py`.

    See also
    --------
    BalanceCascade, EasyEnsemble

    References
    ----------
    .. [1] L. Breiman, "Pasting small votes for classification in large
           databases and on-line", Machine Learning, 36(1), 85-103, 1999.
    .. [2] L. Breiman, "Bagging predictors", Machine Learning, 24(2), 123-140,
           1996.
    .. [3] T. Ho, "The random subspace method for constructing decision
           forests", Pattern Analysis and Machine Intelligence, 20(8), 832-844,
           1998.
    .. [4] G. Louppe and P. Geurts, "Ensembles on Random Patches", Machine
           Learning and Knowledge Discovery in Databases, 346-361, 2012.
    .. [5] Chen, Chao, Andy Liaw, and Leo Breiman. "Using random forest to
           learn imbalanced data." University of California, Berkeley 110,
           2004.
    .. [6] X. Y. Liu, J. Wu and Z. H. Zhou, "Exploratory Undersampling for
           Class-Imbalance Learning," in IEEE Transactions on Systems, Man, and
           Cybernetics, Part B (Cybernetics), vol. 39, no. 2, pp. 539-550,
           April 2009.

    Examples
    --------

    >>> from collections import Counter
    >>> from sklearn.datasets import make_classification
    >>> from sklearn.model_selection import train_test_split
    >>> from sklearn.metrics import confusion_matrix
    >>> from imblearn.ensemble import \
BalancedBaggingClassifier # doctest: +NORMALIZE_WHITESPACE
    >>> X, y = make_classification(n_classes=2, class_sep=2,
    ... weights=[0.1, 0.9], n_informative=3, n_redundant=1, flip_y=0,
    ... n_features=20, n_clusters_per_class=1, n_samples=1000, random_state=10)
    >>> print('Original dataset shape %s' % Counter(y))
    Original dataset shape Counter({{1: 900, 0: 100}})
    >>> X_train, X_test, y_train, y_test = train_test_split(X, y,
    ...                                                     random_state=0)
    >>> bbc = BalancedBaggingClassifier(random_state=42)
    >>> bbc.fit(X_train, y_train) # doctest: +ELLIPSIS
    BalancedBaggingClassifier(...)
    >>> y_pred = bbc.predict(X_test)
    >>> print(confusion_matrix(y_test, y_pred))
    [[ 23   0]
     [  2 225]]

    """

    def __init__(self,
                 base_estimator=None,
                 n_estimators=10,
                 max_samples=1.0,
                 max_features=1.0,
                 bootstrap=True,
                 bootstrap_features=False,
                 oob_score=False,
                 warm_start=False,
                 sampling_strategy='auto',
                 replacement=False,
                 n_jobs=1,
                 random_state=None,
                 verbose=0,
                 ratio=None):

        super(BalancedBaggingClassifier, self).__init__(
            base_estimator,
            n_estimators=n_estimators,
            max_samples=max_samples,
            max_features=max_features,
            bootstrap=bootstrap,
            bootstrap_features=bootstrap_features,
            oob_score=oob_score,
            warm_start=warm_start,
            n_jobs=n_jobs,
            random_state=random_state,
            verbose=verbose)
        self.sampling_strategy = sampling_strategy
        self.ratio = ratio
        self.replacement = replacement

    def _validate_estimator(self, default=DecisionTreeClassifier()):
        """Check the estimator and the n_estimator attribute, set the
        `base_estimator_` attribute."""
        if not isinstance(self.n_estimators, (numbers.Integral, np.integer)):
            raise ValueError("n_estimators must be an integer, "
                             "got {0}.".format(type(self.n_estimators)))

        if self.n_estimators <= 0:
            raise ValueError("n_estimators must be greater than zero, "
                             "got {0}.".format(self.n_estimators))

        if self.base_estimator is not None:
            base_estimator = clone(self.base_estimator)
        else:
            base_estimator = clone(default)

        self.base_estimator_ = Pipeline([('sampler', RandomUnderSampler(
            sampling_strategy=self.sampling_strategy,
            replacement=self.replacement,
            ratio=self.ratio)), ('classifier', base_estimator)])

    def fit(self, X, y):
        """Build a Bagging ensemble of estimators from the training
           set (X, y).

        Parameters
        ----------
        X : {array-like, sparse matrix}, shape (n_samples, n_features)
            The training input samples.

        y : array-like, shape (n_samples,)
            The target values.

        Returns
        -------
        self : object
            Returns self.
        """
        # RandomUnderSampler is not supporting sample_weight. We need to pass
        # None.
        return self._fit(X, y, self.max_samples, sample_weight=None)
