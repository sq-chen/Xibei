import networkx as nx
from collections import deque
from collections import defaultdict
import re
import matplotlib.pyplot as plt
import pandas as pd
from networkx.drawing.nx_pydot import graphviz_layout
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

dict = {}

def chinese_transfer(word):
    res = []
    for w in word:
        res.append(str(ord(w)))
    return 'a'.join(res)

def find_similar_words(edge_file,word):
    result = []
    edge = defaultdict(list)
    f = open(edge_file,"r+",encoding="utf-8").readlines()
    for line in f[1:]:
        line = line.strip("\n").split(" ")
        edge['word1'].append(chinese_transfer(line[0]))
        dict[chinese_transfer(line[0])] = line[0]
        edge['word2'].append(chinese_transfer(line[1]))
        dict[chinese_transfer(line[1])] = line[1]
        edge['cos'].append(float(line[2]))
    edge = pd.DataFrame(edge)
    df = edge[(edge['word1']==word)|(edge['word2']==word)].copy()
    for index,row in df.iterrows():
        if row['word1'] == word:
            result.append((row['word2'], row['cos']))
            continue
        if row['word2'] == word:
            result.append((row['word1'], row['cos']))
    return result


def sim_tree(edge_file, word, max_dist,n_top):
    dict[chinese_transfer(word)] = word   # 根节点
    word = chinese_transfer(word)  # 将根节点的中文转换
    graph = nx.Graph()
    graph.add_node(word, dist=0)
    to_visit = deque([word])
    while len(to_visit) > 0:
        source = to_visit.popleft() # visit next node
        dist = graph.nodes[source]['dist']+1
        model = find_similar_words(edge_file, source)
        if dist <= max_dist: # discover new nodes
            for i in range(len(model)):
                if i == n_top:
                    break
                t = model[i]
                target = t[0]
                sim = t[1]
                if dist == 2 and sim <= 0.2:
                    continue
                if target not in graph:
                    to_visit.append(target)
                    graph.add_node(target, dist=dist)
                    graph.add_edge(source, target, sim=float(sim), dist=int(dist))
                #print(target,source,sim,dist)
    return graph


def plt_add_margin(pos, x_factor=0.1, y_factor=0.1):
    # rescales the image s.t. all captions fit onto the canvas
    x_values, y_values = zip(*pos.values())
    x_max = max(x_values)
    x_min = min(x_values)
    y_max = max(y_values)
    y_min = min(y_values)

    x_margin = (x_max - x_min) * x_factor
    y_margin = (y_max - y_min) * y_factor
    # return (x_min - x_margin, x_max + x_margin), (y_min - y_margin, y_max + y_margin)

    plt.xlim(x_min - x_margin, x_max + x_margin)
    plt.ylim(y_min - y_margin, y_max + y_margin)


def scale_weights(graph, minw=1, maxw=8):
    # rescale similarity to interval [minw, maxw] for display
    sims = [graph[s][t]['sim'] for (s, t) in graph.edges]
    min_sim, max_sim = min(sims), max(sims)

    for source, target in graph.edges:
        sim = graph[source][target]['sim']
        graph[source][target]['sim'] = (sim - min_sim) / (max_sim - min_sim) * (maxw - minw) + minw

    return graph


def solve_graphviz_problems(graph):
    # Graphviz has problems with unicode
    # this is to prevent errors during positioning
    def clean(n):
        n = n.replace(',', '')
        n = n.encode().decode('ascii', errors='ignore')
        n = re.sub(r'[{}\[\]]', '-', n)
        n = re.sub(r'^\-', '', n)
        return n

    node_map = {n: clean(n) for n in graph.nodes}
    # remove empty nodes
    for n, m in node_map.items():
        if len(m) == 0:
            graph.remove_node(n)

    return nx.relabel_nodes(graph, node_map)

rgb = [(180/255,64/255,62/255),(37/255,110/255,162/255), (234/255,132/255,30/255),
       (57/255,147/255,53/255), (96/255,60/255,135/255), (157/255,92/255,57/255)]
def plot_tree(graph, output, node_size=1000, font_size=12):
    graph = solve_graphviz_problems(graph)  ###
    graphviz_path = r"C:\Program Files\Graphviz\bin\twopi.exe"
    pos = graphviz_layout(graph, prog=graphviz_path, root=list(graph.nodes)[0])
    pos = {dict[node]: (float(x), float(y)) for node, (x, y) in pos.items()}

    #print(pos)
    #plt.figure(figsize=(6, 6), dpi=200)  ###
    plt.figure(dpi=200)
    #plt.grid(b=None)  ### hide box
    #plt.box(False)  ### hide grid
    #plt_add_margin(pos)  ### just for layout

    colors = [rgb[int(graph.nodes[n]['dist'])] for n in graph]  # colorize by distance
    node_sizes = [node_size*(5-int(graph.nodes[n]['dist'])) for n in graph]
    #print(colors)
    graph = nx.relabel.relabel_nodes(graph, dict)

    nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, node_color=colors,cmap='Set1', alpha=0.4)
    nx.draw_networkx_labels(graph, pos, font_size=font_size)
    scale_weights(graph)  ### not in book
    for (n1, n2, sim) in graph.edges(data='sim'):
        sim = float(sim)  # 确保 sim 是数值类型
        nx.draw_networkx_edges(graph, pos, [(n1, n2)], width=sim, alpha=0.2)
    plt.tight_layout()
    plt.savefig(output + ".png")
    plt.show()

def draw_tree(edge_file,word,max_dist,n_top,output):
    graph = sim_tree(edge_file=edge_file, word=word,max_dist=max_dist, n_top=n_top)
    plot_tree(graph, node_size=500, font_size=10,output=output)


#draw_tree(edge_file="result/真唱关键词的分析/相关词/超话-0.05高频词的相关词-关键词-名动形.txt",
#          word='真唱', max_dist=3,n_top=5,
#          output='result/真唱关键词的分析/树图/超话-真唱关键词-名动形-1')