class _PlotBase:

    def render(self, *args, **kwargs):
        raise NotImplemented

    def get_legend(self):
        raise NotImplemented

    def get_plot_data(self):
        raise NotImplemented
