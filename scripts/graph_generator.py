import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from networkx.drawing.nx_agraph import graphviz_layout
import tkinter
from persona import FileReader


class GraphGenerator:
    def __init__(self, plot_frame, persona_map):
        self.plot_frame = plot_frame
        self.persona_map = persona_map
        self._canvas = FigureCanvasTkAgg(plt.gcf(), master=self.plot_frame)
        self._canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)
        plt.gcf().set_facecolor("#242424")
        self._pos = None
        self.current_node = None
        self.current_graph = None
        self._counter = 0
        self.file_reader = FileReader()

    def list_to_graph(self, persona_list: list, target_persona):
        plt.gcf().clear()
        list_copy = persona_list.copy()
        # break down all nested lists to end up with one list which contains all required personas
        flatten_list(list_copy)

        # create digraph with all required personas + the result as nodes
        g = nx.DiGraph()
        g.add_node(target_persona)
        g.add_nodes_from(list_copy)
        self._graph_recursive(g, target_persona, persona_list)
        h = self._relabel_fusion_nodes(g)

        # apply tree layout for the graph
        self._pos = graphviz_layout(h, prog='dot')
        print("############")
        print(self._pos)
        nx.draw(h, with_labels=False, pos=self._pos, edge_color="#1F6AA5")
        print(plt.gcf())
        plt.gcf().set_facecolor("#242424")
        for node, (x, y) in self._pos.items():
            if node == self.current_node:
                color = 'red'
            else:
                color = 'white'
            plt.text(x, y, str(node), ha='center', va='center', bbox=dict(facecolor=color, edgecolor='gray',
                                                                          boxstyle='round,pad=0.2'))

        self._canvas.draw()

        # self._canvas.mpl_connect('button_press_event', self._click_node)
        self.current_graph = h
        # plt.draw()
        # plt.show()
        return self._canvas, self._pos

    def _graph_recursive(self, g: nx.DiGraph, root, persona_list: list):
        for p in persona_list:
            if not isinstance(p, list):
                g.add_edge(p, root)
            else:
                # temporary fusion nodes as a placeholder. proper names can only be applied afterwards
                name = f'FUSION{self._counter}'
                self._counter += 1
                g.add_node(name)
                g.add_edge(name, root)
                self._graph_recursive(g, name, p)

    def _relabel_fusion_nodes(self, g: nx.Graph):
        h = g.copy()
        while True:
            nodes = h.copy().nodes()
            for node in nodes:
                # find placeholder fusion nodes
                if str(node).startswith('FUSION'):
                    in_edges = list(h.in_edges(node, data=True))
                    name = None

                    personas = [in_edges[i][0] for i in range(len(in_edges))]
                    special_result = self.file_reader.forward_special_fusion(personas)
                    if special_result is not None:
                        name = special_result.name
                    else:
                        p1 = in_edges[0][0]
                        p2 = in_edges[1][0]
                        # check that both materials (ingoing edges) are named nodes (not fusion or resolved ones)
                        if p1 in self.persona_map.keys() and p2 in self.persona_map.keys():
                            name = self.file_reader.forward_fusion(p1, p2).name
                    # relabel node if possible
                    if name is not None:
                        mapping = {node: name}
                        h = nx.relabel_nodes(h, mapping, copy=False)
            done = True
            for node in h.nodes():
                if str(node).startswith('FUSION'):
                    done = False
            # stop once no nodes starting with FUSION are left
            if done:
                break
        return h


def flatten_list(persona_list):
    while True:
        for p in persona_list:
            if isinstance(p, list):
                persona_list.remove(p)
                persona_list += p
        if not any(isinstance(el, list) for el in persona_list):
            break
