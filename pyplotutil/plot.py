from typing import List, Tuple

import numpy.random as nr
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib

import seaborn as sns

from sklearn import metrics

__all__ = [
    'roc_curve',
    'roc_plot',
    'precision_recall_curve',
    'precision_recall_plot',
    'average_precision_recall',
    'average_auPRC',
    'average_precision_recall_curve',
    'tp_at_k',
    'tp_at_k_curve',
    'tp_at_k_plot',
    'density_scatter',
]


def _prc_step(precision, recall, sklearn_mode=True):
    if not sklearn_mode:
        # make sure that input is sorted by recall
        idx = np.argsort(recall)
    else:
        # by default, sklearn reports recall sorted descending
        # => just inverting in this case is faster
        idx = slice(None, None, -1)

    prec_step = np.zeros((len(precision) * 2) - 1)
    rec_step = np.zeros((len(recall) * 2) - 1)

    prec_step[np.arange(len(precision)) * 2] = precision[idx]
    rec_step[np.arange(len(recall)) * 2] = recall[idx]

    # resemble 'post' step plot
    prec_step[np.arange(len(recall) - 1) * 2 + 1] = precision[idx][1:]
    rec_step[np.arange(len(recall) - 1) * 2 + 1] = recall[idx][:-1]

    return prec_step, rec_step


def roc_curve(y_true, y_pred, label, formatting='%s (auROC = %0.2f%%)', type="step", where="post"):
    # Compute False postive rate, and True positive rate
    fpr, tpr, thresholds = metrics.roc_curve(y_true, y_pred)
    # Calculate Area under the curve to display on the plot
    auc = metrics.roc_auc_score(y_true, y_pred)
    # Now, plot the computed values
    if type == "step":
        plt.step(fpr, tpr, label=formatting % (label, 100 * auc), where=where)
    elif type == "line":
        plt.plot(fpr, tpr, label=formatting % (label, 100 * auc))
    else:
        raise ValueError("Unknown curve type %s" % type)


def roc_plot(y_trues, y_preds: list, labels=None, add_random_shuffle=False, legend_pos="inside", **kwargs):
    plt.figure()

    if not isinstance(y_preds, list) and not np.ndim(y_preds) > 1:
        y_preds = [y_preds]

    if not isinstance(y_trues, list) and not np.ndim(y_trues) > 1:
        y_trues = [y_trues] * len(y_preds)

    if isinstance(y_preds, pd.DataFrame):
        if labels is None:
            labels = y_preds.columns.astype(str)
    else:
        if labels is None:
            labels = np.arange(1, np.shape(y_preds)[1] + 1)
    labels = np.asarray(labels).flatten()

    # convert DataFrame to list
    if isinstance(y_preds, pd.DataFrame):
        y_preds = [v.values for k, v in y_preds.items()]

    formatting = '%s (auROC = %0.2f%%)' if legend_pos == "inside" else '%s\n(auROC = %0.2f%%)'

    # Below for loop iterates through your models list
    for l, y_true, y_pred in zip(labels, y_trues, y_preds):
        roc_curve(y_true, y_pred, label=l, formatting=formatting, **kwargs)

    if add_random_shuffle:
        y_true = np.concatenate(y_trues)
        rng = np.random.default_rng(42)

        roc_curve(y_true, rng.choice(y_true, len(y_true)), label="random shuffle", formatting=formatting, **kwargs)

    # Custom settings for the plot
    plt.plot([0, 1], [0, 1], 'r--')
    # plt.grid()
    plt.xlabel('False Positive Rate FP/TN+FP')
    plt.ylabel('True Positive Rate TP/TP+FP')
    plt.title('Receiver Operating Characteristic')

    if legend_pos == "inside":
        plt.legend(loc=4)
    else:
        plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    # plt.tight_layout()

    return plt.gcf()


def precision_recall_curve(y_true, y_pred, label, formatting='%s (auc = %0.2f%%)',
                           type="step", where="post", binary_as_point=True):
    # Calculate Area under the curve to display on the plot
    auc = metrics.average_precision_score(y_true=y_true, y_score=y_pred)

    if binary_as_point:
        min_y_pred = np.min(y_pred)
        max_y_pred = np.max(y_pred)

        if np.all(np.isin(y_pred, [min_y_pred, max_y_pred])):
            # y_pred is a binary predictor
            binarized_y_pred = y_pred == max_y_pred

            recall = [metrics.recall_score(y_true, binarized_y_pred)]
            precision = [metrics.precision_score(y_true, binarized_y_pred)]

            # plot a single point instead of a curve
            plt.scatter(recall, precision, marker='x', label=formatting % (label, 100 * auc))

            return

    # Compute precision and recall
    precision, recall, thresholds = metrics.precision_recall_curve(y_true=y_true, probas_pred=y_pred)

    # Now, plot the computed values
    if type == "step":
        plt.step(recall, precision, label=formatting % (label, 100 * auc), where=where)
    elif type == "line":
        plt.plot(recall, precision, label=formatting % (label, 100 * auc))
    else:
        raise ValueError("Unknown curve type %s" % type)


def precision_recall_plot(
        y_trues,
        y_preds,
        labels=None,
        add_random_shuffle=True,
        add_average=False,
        legend_pos="inside",
        xlim=(-0.05, 1.05),
        ylim=(-0.05, 1.05),
        **kwargs
):
    plt.figure()

    if not isinstance(y_preds, list) and not np.ndim(y_preds) > 1:
        y_preds = [y_preds]

    if not isinstance(y_trues, list) and not np.ndim(y_trues) > 1:
        y_trues = [y_trues] * len(y_preds)

    # infer labels
    if isinstance(y_preds, pd.DataFrame):
        if labels is None:
            labels = y_preds.columns.astype(str)
    else:
        if labels is None:
            labels = np.arange(1, np.shape(y_preds)[1] + 1)
    labels = np.asarray(labels).flatten()

    # convert DataFrame to list
    if isinstance(y_preds, pd.DataFrame):
        y_preds = [v.values for k, v in y_preds.items()]

    formatting = '%s (auc = %0.2f%%)' if legend_pos == "inside" else '%s\n(auc = %0.2f%%)'

    # Below for loop iterates through your models list
    for l, y_true, y_pred in zip(labels, y_trues, y_preds):
        precision_recall_curve(y_true, y_pred, label=l, formatting=formatting, **kwargs)

    if add_random_shuffle:
        y_true = np.concatenate(y_trues)
        rng = np.random.default_rng(42)

        precision_recall_curve(y_true, rng.choice(y_true, len(y_true)), label="random shuffle",
                               formatting=formatting, **kwargs)

    if add_average:
        average_precision_recall_curve(y_truecats=y_trues, y_preds=y_preds, label="average",
                                       formatting=formatting, **kwargs)

    # Custom settings for the plot
    # plt.grid()
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.xlabel("recall TP/(TP+FN)")
    plt.ylabel("precision TP/(TP+FP)")
    plt.title("Precision vs. Recall")

    if legend_pos == "inside":
        plt.legend(loc="center right")
        # plt.legend(loc="upper right")
    else:
        plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    # plt.tight_layout()

    return plt.gcf()


def average_precision_recall(y_preds: List[np.ndarray], y_truecats: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate the average precision recall values given a list of predictions

    :param y_preds: list of model predictions
    :param y_truecats: list of categorical y_true's for the model predictions
    :returns: precision, recall
    """
    # calculate (precision, recall, thresholds) for every prediction
    prcs = [
        metrics.precision_recall_curve(
            y_true=y_truecat,
            probas_pred=y_pred,
        ) for y_pred, y_truecat in zip(y_preds, y_truecats)
    ]

    # number of positives per prediction
    n_positives = [y_truecat.sum().item() for y_truecat in y_truecats]

    # proportion of positive values per prediction, compared to the total number of positives
    props = np.asarray(n_positives)
    props = props / np.sum(props)

    # apply step-function to get correct precision recall curve
    stepped = [
        _prc_step(precision, recall)
        for precision, recall, thresholds in prcs
    ]

    # interpolate step functions s.t. we can get precision for an arbitrary recall value
    import scipy.interpolate
    fs = [scipy.interpolate.interp1d(x=recall, y=precision, kind="next") for precision, recall in stepped]

    # get union of all recalls
    recalls = [p[1] for p in prcs]
    union_recall = np.sort(np.unique(np.concatenate(recalls)))[::-1]

    # Compute the average precision as the weighted mean of all prediction's precision values.
    # Use the union of all recalls to interpolate the precisions:
    #     precision = f(recall)
    # Weight by the total number of positives, since `recall = tps / n_positive`
    precisions = [f(union_recall) for f in fs]
    precisions = np.asarray(precisions)
    ave_precision = np.sum(props * precisions.T, axis=-1)

    return ave_precision, union_recall


def average_auPRC(y_preds: List[np.ndarray], y_truecats: List[np.ndarray]) -> float:
    """
    Calculate the average area under precision recall (auPRC) values given a list of predictions.

    TODO: needs test like this:
    ```python
        precision, recall = average_precision_recall(
            y_preds = [-pred["y_pred"] for pred in valid_preds],
            y_truecats = [pred["y_truecat"] for pred in valid_preds],
        )

        a, b = _prc_step(precision, recall)
        apr_auc = sklearn.metrics.auc(b, a)

        ave_auPRC = average_auPRC(
            y_preds = [-pred["y_pred"] for pred in valid_preds],
            y_truecats = [pred["y_truecat"] for pred in valid_preds],
        )
        assert np.close(ave_auPRC, apr_auc)
    ```

    :param y_preds: list of model predictions
    :param y_truecats: list of categorical y_true's for the model predictions
    :returns: average auPRC
    """
    # calculate (precision, recall, thresholds) for every prediction
    auPRCs = [
        metrics.average_precision_score(
            y_true=y_truecat,
            y_score=y_pred,
        ) for y_pred, y_truecat in zip(y_preds, y_truecats)
    ]

    # number of positives per prediction
    n_positives = [y_truecat.sum().item() for y_truecat in y_truecats]

    # proportion of positive values per prediction, compared to the total number of positives
    props = np.asarray(n_positives)
    props = props / np.sum(props)

    ave_auPRC = np.sum(props * auPRCs)

    return ave_auPRC


def average_precision_recall_curve(
        y_truecats: List[np.ndarray],
        y_preds: List[np.ndarray],
        label,
        formatting='%s (auc = %0.2f%%)',
        type="step",
        where="post"
):
    # Compute precision and recall
    precision, recall = average_precision_recall(y_truecats=y_truecats, y_preds=y_preds)
    # Calculate Area under the curve to display on the plot
    auc = average_auPRC(y_truecats=y_truecats, y_preds=y_preds)
    # Now, plot the computed values
    if type == "step":
        plt.step(recall, precision, label=formatting % (label, 100 * auc), where=where)
    elif type == "line":
        plt.plot(recall, precision, label=formatting % (label, 100 * auc))
    else:
        raise ValueError("Unknown curve type %s" % type)


def tp_at_k(observed, score):
    df = pd.DataFrame(dict(observed=observed, score=score))
    df = df.sort_values(by="score", ascending=False).reset_index()
    df["n_true"] = df["observed"].cumsum()
    df["k"] = df.index

    return df


def tp_at_k_curve(y_true, y_pred, label, formatting='%s (auc = %0.2f%%)', y_true_sum=None, type="step", where="post"):
    if not y_true_sum:
        y_true_sum = np.asarray(np.sum(y_true))

    # Compute precision at k
    df = tp_at_k(y_true, y_pred)
    # Calculate Area under the curve to display on the plot
    auc = metrics.auc(df["k"] / len(y_true), df["n_true"] / y_true_sum)
    # Now, plot the computed values
    if type == "step":
        plt.step(df["k"], df["n_true"], label=formatting % (label, 100 * auc), where=where)
    elif type == "line":
        plt.plot(df["k"], df["n_true"], label=formatting % (label, 100 * auc))
    else:
        raise ValueError("Unknown curve type %s" % type)


def tp_at_k_plot(y_trues, y_preds, labels=None, add_random_uniform=False, legend_pos="inside", **kwargs):
    plt.figure()

    if not isinstance(y_preds, list) and not np.ndim(y_preds) > 1:
        y_preds = [y_preds]

    # calculate sum only if there is only a single y_true array
    y_true_sum = None
    if not isinstance(y_trues, list) and not np.ndim(y_trues) > 1:
        y_true_sum = np.asarray(np.sum(y_trues))
        y_trues = [y_trues] * len(y_preds)

    if isinstance(y_preds, pd.DataFrame):
        if labels is None:
            labels = y_preds.columns.astype(str)
    else:
        if labels is None:
            labels = np.arange(1, np.shape(y_preds)[1] + 1)
    labels = np.asarray(labels).flatten()

    # convert DataFrame to list
    if isinstance(y_preds, pd.DataFrame):
        y_preds = [v.values for k, v in y_preds.items()]

    formatting = '%s (auc = %0.2f%%)' if legend_pos == "inside" else '%s\n(auc = %0.2f%%)'

    # Below for loop iterates through your models list
    for l, y_true, y_pred in zip(labels, y_trues, y_preds):
        tp_at_k_curve(y_true, y_pred, label=l, formatting=formatting, y_true_sum=y_true_sum, **kwargs)

    if add_random_uniform:
        tp_at_k_curve(y_true, np.random.uniform(size=len(y_true)), label="random uniform", formatting=formatting,
                      y_true_sum=y_true_sum, **kwargs)

    # Custom settings for the plot
    plt.plot([0, len(y_true)], [0, y_true_sum], 'r--')
    plt.xlabel("k (rank of score)")
    plt.ylabel("number of true positives")
    plt.title("True Positives at k")

    if legend_pos == "inside":
        plt.legend(loc=4)
    else:
        plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    # plt.tight_layout()

    return plt.gcf()


def density_scatter(
        x,
        y,
        data: pd.DataFrame = None,
        xlab="x",
        ylab="y",
        xlim=None,
        ylim=None,
        sort=True,
        bins=1000,
        marker_size=1,
        marker_linewidth=0,
        marker_colornorm=None,
        rasterized=True,
        interpolate_density=False,
        normalize_density=True,
        kde=False,
        scatter_kwargs=None,
        marginals_kwargs=None,
        jointgrid_kwargs=None,
        **kwargs
):
    """
    Scatter plot colored by 2d histogram.

    Example:
        ```
        g = density_scatter(
            x=m.predicted.values,
            y=m.zscore.values,
            ylab='z-score (difference to mean)\nlung',
            xlab='prediction score\nlung',
            jointgrid_kwargs=dict(
                xlim=[-10, 10], # x-axis limits
                ylim=[-10, 10], # x-axis limits
            ),
            scatter_kwargs=dict(
                rasterized=True, # do not use vector graphics for scatter plot
                norm=matplotlib.colors.LogNorm(), # log-scale for point density
                sizes=(1, 1), # point size
            ),
        )
        g.fig.suptitle(model)
        plt.show()
        ```
    """
    if data is not None:
        x = data.loc[:, x].values
        y = data.loc[:, y].values

    from scipy.interpolate import interpn
    xy = pd.DataFrame({xlab: x, ylab: y})
    xy = xy.dropna().reset_index(drop=True)
    # keep data as pandas series for axis labels (!)
    x: pd.Series = xy[xlab]
    y: pd.Series = xy[ylab]

    # calculate 2D histogram
    data, x_e, y_e = np.histogram2d(x, y, bins=bins)

    if interpolate_density:
        # interpolate every point based on the distance to the neighbouring bin
        z: np.ndarray = interpn(
            (
                0.5 * (x_e[1:] + x_e[:-1]),
                0.5 * (y_e[1:] + y_e[:-1])
            ),
            data,
            xy,
            method="splinef2d",
            bounds_error=False,
            fill_value=0
        )
    else:
        z = data[
            (np.argmax(np.expand_dims(x, -1) <= x_e[1:], axis=-1)),
            (np.argmax(np.expand_dims(y, -1) <= y_e[1:], axis=-1)),
        ]

    if normalize_density:
        # normalize minimal value to 1, especially important for logarithmic color scale
        z = z - np.min(z) + 1

    # Sort the points by density, so that the densest points are plotted last
    if sort:
        idx = z.argsort()
        x = x.iloc[idx]
        y = y.iloc[idx]
        z = z[idx]

    # set default scatter_kwargs
    combined_scatter_kwargs = dict(
        s=marker_size,
        linewidth=marker_linewidth,
        rasterized=rasterized,
    )
    if marker_colornorm:
        if (type(marker_colornorm) == str) and marker_colornorm.lower() == "log":
            combined_scatter_kwargs["norm"] = matplotlib.colors.LogNorm()
        else:
            combined_scatter_kwargs["norm"] = marker_colornorm
    # default scatter_kwargs will be overridden by user-defined options
    if scatter_kwargs is not None:
        for k, v in scatter_kwargs.items():
            combined_scatter_kwargs[k] = v

    # set up default jointgrid args
    combined_jointgrid_kwargs = dict()
    if xlim:
        combined_jointgrid_kwargs["xlim"] = xlim
    if ylim:
        combined_jointgrid_kwargs["ylim"] = ylim
    # default jointgrid_kwargs will be overridden by user-defined options
    if jointgrid_kwargs is not None:
        combined_jointgrid_kwargs.update(jointgrid_kwargs)

    combined_marginals_kwargs = dict(
        bins=bins,  # per default same number of bins as for the hist2d
        kde=kde,  # kde takes a long time to calculate
    )
    # default marginals_kwargs will be overridden by user-defined options
    if "distplot_kwargs" in kwargs:
        if marginals_kwargs is None:
            marginals_kwargs = dict()
        marginals_kwargs.update(kwargs["distplot_kwargs"])
    if marginals_kwargs is not None:
        combined_marginals_kwargs.update(marginals_kwargs)

    # create the JointGrid
    g = sns.JointGrid(x=x, y=y, **combined_jointgrid_kwargs)
    g = g.plot_marginals(sns.histplot, **combined_marginals_kwargs)
    # hack to get the correct coordinates set in plt.scatter
    g.x = x
    g.y = y
    g = g.plot_joint(plt.scatter, c=z, **combined_scatter_kwargs)
    # shrink fig so cbar is visible
    plt.subplots_adjust(left=0.2, right=0.8, top=0.8, bottom=0.2)
    # make new ax object for the cbar
    cbar_ax = g.fig.add_axes([.85, .25, .05, .4])  # x, y, width, height
    plt.colorbar(cax=cbar_ax)
    return g
