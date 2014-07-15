from __future__ import print_function # For py 2.7 compat

from IPython.html import widgets # Widget definitions
from IPython.display import display # Used to display widgets in the notebook
from IPython.utils.traitlets import Unicode, List, Dict, Int, Bool # Used to declare attributes of our widget
from IPython.display import HTML


_rolling_chart_html = r'''
<script src="http://nvd3.org/assets/lib/d3.v3.js"></script>
<script src="http://nvd3.org/assets/js/nv.d3.js"></script>
<style>

svg {
  padding-left: 50px;
  margin-left: 50px;
  font: 10px sans-serif;
}

div.chart {
 background-color: rgb(140,140,140);
 width: 800px;
 height: 500px;
}

.line {
  fill: none;
  stroke: rgb(136,189,230);
  stroke-width: 1.5px;
}

.axis path,
.axis line {
  fill: none;
  stroke: rgb(250,154,58);
  shape-rendering: crispEdges;
}
.axis text {
  fill: white;
  shape-rendering: crispEdges;
}
</style>

<script>
window.RollingChart = function(d3_root, data, domain, interpolation) {
  var self = this;
  self.$data = data;
  self.$d3_root = d3_root;
//   var shape = {width: +d3_root.style('width').replace('px', ''),
//                height: +d3_root.style('height').replace('px', '')};
  var shape = {width: 700, height: 500};
  console.log(shape);
  self.$margin = {top: 15, right: 40, bottom: 50, left: 40},
      self.$width = shape.width - self.$margin.right,
      self.$height = shape.height - self.$margin.top - self.$margin.bottom;

  self.x = d3.scale.linear().domain(domain.x).range([0, self.$width]);
  self.y = d3.scale.linear().domain(domain.y).range([self.$height, 0]);

  self.$line = d3.svg.line()
      .interpolate(interpolation)
      .x(function(d, i) { return self.x(i); })
      .y(function(d, i) { return self.y(d); });

  self.$svg = d3_root.append("svg")
      .attr("width", self.$width + self.$margin.left + self.$margin.right)
      .attr("height", self.$height + self.$margin.top + self.$margin.bottom)
      .style("margin-left", self.$margin.left + "px")
    .append("g")
      .attr("transform", "translate(" + self.$margin.left + "," +
            self.$margin.top + ")");

  self.$svg.append("defs").append("clipPath")
      .attr("id", "clip")
    .append("rect")
      .attr("width", self.$width)
      .attr("height", self.$height);

  self.$svg.append("g")
      .attr("class", "y axis")
      .call(d3.svg.axis().scale(self.y).ticks(5).orient("left"));

  self.$path = self.$svg.append("g")
      .attr("clip-path", "url(#clip)")
    .append("path")
      .data([data])
      .attr("class", "line")
      .attr("d", self.$line);
}
</script>'''

_rolling_chart_javascript = r'''
<script>
require(["widgets/js/widget"], function(WidgetManager){
    var RollingChartView = IPython.DOMWidgetView.extend({
        render: function(){
            var self = this;
            /* Apply this class to the widget container to make it fit with the other built in widgets.*/
            this.$el.addClass("chart");
            self.$d3_el = d3.select(this.$el[0]);
            self.$d3_el.datum(self)
            this.$control_group = self.$d3_el.append('div').attr('class', 'btn-group analog-read-control');
            (this.$control_group
             .append('button').attr('type', 'button')
                 .attr('class', 'btn btn-default btn-lg analog-read-start')
                 .on('click', $.proxy(this.start, self))
             .append('i').attr('class', 'icon-play'));
             //.append('span').attr('class', 'glyphicon glyphicon-play'));
            (this.$control_group
             .append('button').attr('type', 'button')
                 .attr('class', 'btn btn-default btn-lg analog-read-stop')
                 .on('click', $.proxy(this.stop, self))
             .append('i').attr('class', 'icon-stop'));
             //.append('span').attr('class', 'glyphicon glyphicon-stop'));

            self.$chart = new RollingChart(self.$d3_el,
                                           d3.range(100).map(function () { return 0; }),
                                           {x: [1, 100 - 2], y: [0, 1024]},
                                           "basis");
        },

        tick: function() {
            var self = this;
            var command = (self.model.get('board_variable') +
                           '.analog_read(pin=' +
                           self.model.get('analog_pin') + ')');
            IPython.notebook.kernel
            .execute(command,
                     {"iopub": {"output": function (msg) {
                         self.update_value(+msg.content.data['text/plain'].replace('L', '')); }}},
                     {silent: false});
        },

        update: function() {
          var self = this;
          return RollingChartView.__super__.update.apply(this);
        },

        start: function () {
            console.log(this);
            this.model.set('stream', true);
            this.touch();
            this.update_value(this.model.get('value'));
        },

        stop: function () {
            this.model.set('stream', false);
            this.touch();
        },

        update_value: function (value) {
            var self = this;
            self.$chart.$data.push(+value);
            this.model.set('value', +value);
            this.touch();
            // redraw the line, and then slide it to the left
            var cycle_period_ms = +this.model.get('cycle_period_ms');
            var transition = self.$chart.$path.attr("d", self.$chart.$line)
                .attr("transform", null)
              .transition()
                .duration(cycle_period_ms)
                .ease("linear")
                .attr("transform", "translate(" + self.$chart.x(0) + ")")
            var stream = this.model.get('stream');
            if (stream) {
                transition.each("end", $.proxy(self.tick, self));
            }

            // pop the old data point off the front
            self.$chart.$data.shift();
        }
    });


    // Register the DatePickerView with the widget manager.
    WidgetManager.register_widget_view('RollingChartView', RollingChartView);
});
</script>
'''


display(HTML(_rolling_chart_html + _rolling_chart_javascript))


class RollingChartWidget(widgets.DOMWidget):
    _view_name = Unicode('RollingChartView', sync=True)
    positions = List(sync=True, trait=Dict)
    value = Int(sync=True)
    stream = Bool(sync=True)
    board_variable = Unicode(sync=True, default_value='board')
    analog_pin = Int(sync=True, default_value=0)
    cycle_period_ms = Int(sync=True, default_value=150)

    def __init__(self, **kwargs):
        super(RollingChartWidget, self).__init__(**kwargs)

        self.validate = widgets.CallbackDispatcher()

    # This function automatically gets called by the traitlet machinery when
    # value is modified because of this function's name.
    def _value_changed(self, name, old_value, new_value):
        self.value = new_value
