/*jslint browser: true*/
/*global $, jQuery*/

var g_nodes = new vis.DataSet();
var g_edges = new vis.DataSet();

var nodes = [
    {"id": 1, "ip": "192.168.2.21", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "plc": "no_plc", "role": "mp"},
    {"id": 2, "ip": "192.168.2.22", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "plc": "no_plc", "role": "gw"},
    {"id": 3, "ip": "192.168.2.23", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "plc": "no_plc", "role": "mp"},
    {"id": 4, "ip": "192.168.2.24", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "plc": "no_plc", "role": "mp"},
    {"id": 5, "ip": "192.168.2.25", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "plc": "no_plc", "role": "sta_5g"},
    {"id": 6, "ip": "192.168.2.26", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "1x1", "plc": "no_plc", "role": "mp"},
    {"id": 7, "ip": "192.168.2.27", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "plc": "no_plc", "role": "none"}
];

function node_by_id(id) {
    for (var i = nodes.length - 1; i >= 0; i--) {
        if (nodes[i].id === id) {
            return nodes[i];
        }
    }
}

function get_test_wifi(src, dest, chain_src, chain_dst, band, bw) {
    "use strict";
    if (chain_src === "1x1" && chain_dst === "2x2") {
        chain_dst = "1x1";
    } else if (chain_src === "1x1" && chain_dst === "3x3") {
        chain_dst = "1x1";
    } else if (chain_src === "2x2" && chain_dst === "3x3") {
        chain_dst = "2x2";
    }

    var dat = test_data.filter(function (x) {
        return (x.src === src &&
                x.dest === dest &&
                x.chain_src === chain_src &&
                x.chain_dst === chain_dst &&
                x.band === band &&
                x.bw === bw
               );
    });
    if (dat.length === 0) {
        return 0.0001; //avoid divide by zero lol
    }
    return dat[0].dat;
}

function get_test_plc(src, dest) {
    "use strict";
    var dat = test_data.filter(function (x) {
        return (x.src === src &&
                x.dest === dest &&
                x.band === 'mimo_plc'
               );
    });
    if (dat.length === 0) {
        return 0.0001; //avoid divide by zero lol
    }
    return dat[0].dat;
}

function color_node(id) {
    "use strict";
    var role = node_by_id(id).role;
    if (role === "sta_2g") {
        g_nodes.update({id: id, color: 'red'});
    } else if (role === "sta_5g") {
        g_nodes.update({id: id, color: 'green'});
    } else if (role === "gw") {
        g_nodes.update({id: id, color: 'yellow'});
    } else if (role === "none") {
        g_nodes.update({id: id, color: 'gray'});
    } else {
        g_nodes.update({id: id, color: 'pink'});
    }
}

function change_role(id) {
    "use strict";
    var new_role = $("#role_" + id).val();
    node_by_id(id).role = new_role;
    if (new_role === "sta_2g") {
        $("#ch_2g_" + id).css({"visibility":"visible"});
        $("#bw_2g_" + id).css({"visibility":"visible"});
        $("#ch_5g_" + id).css({"visibility":"hidden"});
        $("#bw_5g_" + id).css({"visibility":"hidden"});
        $("#plc_" + id).css({"visibility":"hidden"});
    } else if (new_role === "sta_5g") {
        $("#ch_2g_" + id).css({"visibility":"hidden"});
        $("#bw_2g_" + id).css({"visibility":"hidden"});
        $("#ch_5g_" + id).css({"visibility":"visible"});
        $("#bw_5g_" + id).css({"visibility":"visible"});
        $("#plc_" + id).css({"visibility":"hidden"});
    } else if (new_role === "none") {
        $("#ch_2g_" + id).css({"visibility":"hidden"});
        $("#bw_2g_" + id).css({"visibility":"hidden"});
        $("#ch_5g_" + id).css({"visibility":"hidden"});
        $("#bw_5g_" + id).css({"visibility":"hidden"});
        $("#plc_" + id).css({"visibility":"hidden"});
    } else {
        $("#ch_2g_" + id).css({"visibility":"visible"});
        $("#bw_2g_" + id).css({"visibility":"visible"});
        $("#ch_5g_" + id).css({"visibility":"visible"});
        $("#bw_5g_" + id).css({"visibility":"visible"});
        $("#plc_" + id).css({"visibility":"visible"});
    }
    color_node(id);
}

function change_plc(id) {
    "use strict";
    node_by_id(id).plc = $("#plc_" + id).val();
}

function change_bw_2g(id) {
    "use strict";
    node_by_id(id).bw_2g = $("#bw_2g_" + id).val();
}

function change_bw_5g(id) {
    "use strict";
    node_by_id(id).bw_5g = $("#bw_5g_" + id).val();
}

function change_chain_5g(id) {
    "use strict";
    node_by_id(id).chain_5g = $("#ch_5g_" + id).val();
}

function change_chain_2g(id) {
    "use strict";
    node_by_id(id).chain_2g = $("#ch_2g_" + id).val();
}

function change_chain_5g(id) {
    "use strict";
    node_by_id(id).chain_5g = $("#ch_5g_" + id).val();
}

function get_src_dst_pairs() {
    "use strict";
    var srcs = [];
    var dests = [];
    var pairs = [];

    for (var i = 0; i < nodes.length; i++) {
        if (nodes[i].role === "sta_2g" || nodes[i].role === "sta_5g") {
            dests.push(i);
        } else if (nodes[i].role === "gw") {
            srcs.push(i);
        }
    }

    srcs.forEach(function (src) {
        dests.forEach(function (dest) {
            pairs.push({"src" : src, "dest" : dest});
        });
    });

    return pairs;
}

function get_mps() {
    "use strict";
    var mps = [];
    for (var i = 0; i < nodes.length; i++) {
        if (nodes[i].role === "mp") {
            mps.push(i);
        }
    }
    return mps;
}

function get_perms(arr, l) {
    "use strict";
    var i = 0;
    var len = 0;
    if (l === 1) {
        var res = [];
        arr.forEach(function (item) {
            res.push([item]);
        });
        return res;
    }

    var perm_list = [];
    for (i = 0, len = arr.length; i < len; i++) {
        var small_arr = arr.slice();
        var elem = small_arr.splice(i, 1);
        var sub_perms = get_perms(small_arr, l - 1);

        for (i = 0, len = sub_perms.length; i < len; i++) {
            perm_list.push(elem.concat(sub_perms[i]));
        }

    }
    return perm_list;
}

function hop_calc_tput(hop) {
    "use strict";
    var src_node = nodes[hop.src];
    var dest_node = nodes[hop.dest];
    var dat = 0.0001;

    var bw = "bw20";

    if (hop.band === "2g") {
        if (src_node.bw_2g < dest_node.bw_2g) {
            bw = src_node.bw_2g;
        } else {
            bw = dest_node.bw_2g;
        }
        dat = get_test_wifi(src_node.ip, dest_node.ip, src_node.chain_2g, dest_node.chain_2g, hop.band, bw);
    } else if (hop.band === "5g") {
        if (src_node.bw_5g < dest_node.bw_5g) {
            bw = src_node.bw_5g;
        } else {
            bw = dest_node.bw_5g;
        }
        dat = get_test_wifi(src_node.ip, dest_node.ip, src_node.chain_5g, dest_node.chain_5g, hop.band, bw);
    } else if (hop.band === "plc") {
        dat = get_test_plc(src_node.ip, dest_node.ip);
    }

    hop.tput = dat;
}

function calculate_path_cost(path) {
    "use strict";
    var cost = 0.0;
    path.forEach(function (hop) {
        cost += 1.0 / hop.tput;
    });
    return cost;
}

function pretty_num(num) {
    var val = Math.round(num * 100) / 100;
    return val.toString();
}

function path_to_str(path) {
    "use strict";
    var res_str = "";
    var cost = 0;
    path.forEach(function (hop) {
        cost += 1 / hop.tput;
        res_str += " (" + nodes[hop.src].id + " -> " + nodes[hop.dest].id + " , " + pretty_num(hop.tput) + ")";
    });

    res_str = pretty_num(1 / cost) + " Mbps " + res_str;
    return res_str;
}

function path_to_edges(path) {
    "use strict";
    var new_edges = [];
    path.forEach(function (hop) {
        new_edges.push({from: nodes[hop.src].id, to: nodes[hop.dest].id, label: pretty_num(hop.tput)});
    });
    g_edges.add(new_edges);
}

function nth_bit(in_val, n) {
    return (in_val >> n) & 1;
}

function get_all_links(link_cnt) {
    var link_arr = [];
    for (var i = 0; i < Math.pow(2, link_cnt); i++) {
        var new_arr = [];
        for (var j = 0; j < link_cnt; j++) {
            if (nth_bit(i, j) === 1) {
                new_arr.push('5g');
            } else {
                new_arr.push('plc');
            }
        }
        link_arr.push(new_arr);
    }
    return link_arr;
}

function find_best_route(src_idx, dest_idx, mps) {
    "use strict";
    var route_nodes = [[]];
    var i = 0;
    var len = 0;
    //fill route_nodes with all possible stopping points between src and dest
    for (i = 0, len = mps.length + 1; i < len; i++) {
        //route_nodes.push(get_perms(mps, i));
        route_nodes = route_nodes.concat(get_perms(mps, i));
    }

    var costs = [];
    var paths = [];

    //convert route_nodes to hop objects with "src", "dest" , "tput"
    route_nodes.forEach(function (route) {
        var all_links = get_all_links(route.length);

        for (var i = 0; i < all_links.length; i++) {
            var hops = [];
            var current_node = src_idx;
            for (var j = 0; j < route.length; j++) {
                var hop = {"src" : current_node, "dest" : route[j], "tput" : 0, "band" : all_links[i][j]};
                hop_calc_tput(hop);
                hops.push(hop);
                current_node = route[j];
            }

            var hop_last = {"src" : current_node, "dest" : dest_idx, "tput": 0, "band" : "2g"};
            if (nodes[dest_idx].role === 'sta_5g') {
                hop_last.band = "5g";
            }
            hop_calc_tput(hop_last);
            hops.push(hop_last);
            paths.push(hops);
        }
    });

    paths.forEach(function (path) {
        costs.push(calculate_path_cost(path));
    });

    var min_idx = costs.indexOf(Math.min.apply(Math, costs));

    //console.log(paths);
    return paths[min_idx];
}

function calculate_routes() {
    "use strict";
    var pairs = get_src_dst_pairs();
    var mps = get_mps();

    var disp_str = "";

    g_edges.clear();

    pairs.forEach(function (pair) {
        var best = find_best_route(pair.src, pair.dest, mps);
        disp_str += nodes[pair.src].id + " -> " + nodes[pair.dest].id + " ==> " + path_to_str(best) + "\n";
        path_to_edges(best);
        console.log(best);
    });
    $("#result").val(disp_str);
}

function test() {
    "use strict";
    graph_test();
    nodes.forEach(function (node) {
        color_node(node.id);
    });
}

function graph_test() {
    // create an array with nodes
    g_nodes.add([
        {id: 1 , label: '1' , y: -135 , x: 10  , allowedToMoveX: true , allowedToMoveY: true},
        {id: 2 , label: '2' , y: 72   , x: 200 , allowedToMoveX: true , allowedToMoveY: true},
        {id: 3 , label: '3' , y: 130  , x: 27 , allowedToMoveX: true , allowedToMoveY: true},
        {id: 4 , label: '4' , y: 239  , x: -39   , allowedToMoveX: true , allowedToMoveY: true} ,
        {id: 5 , label: '5' , y: 268  , x: -372   , allowedToMoveX: true , allowedToMoveY: true},
        {id: 6 , label: '6' , y: 73   , x: -184 , allowedToMoveX: true , allowedToMoveY: true},
        {id: 7 , label: '7' , y: -136 , x: -230 , allowedToMoveX: true , allowedToMoveY: true},
    ]);

    //g_edges.add([{from: 2, to: 1}]);
    g_edges.add([]);

    // create a network
    var container = document.getElementById('mynetwork');
    var data = {
        nodes: g_nodes,
        edges: g_edges
    };

    var options = {
        //dragNetwork: false,
        //dragNodes: false,
        edges: {
            color: 'green',
            style: 'arrow',
            width: 4
        },
        physics: {barnesHut: {gravitationalConstant: 0, centralGravity: 0, springConstant: 0}},
        zoomable: false
    };
    var network = new vis.Network(container, data, options);
    network.on('dragEnd', function() {
        this.storePositions();
        console.log(JSON.stringify(this.getPositions()));
    });

    network.on('select', function(properties) {
        var node = node_by_id(parseInt(properties.nodes[0]));
        if (properties.nodes.length === 0) {
            $("#aptable").html("");
            return;
        }
        var html_str = "<tr>";
        html_str += "<td>";
        html_str += node.id;
        html_str += "</td>";
        html_str += "<td>";
        html_str += "<select onchange=\"change_role(" + node.id + ")\" id=\"role_" + node.id + "\"></select>";
        html_str += "<select onchange=\"change_plc(" + node.id + ")\" id=\"plc_" + node.id + "\"></select>";
        html_str += "</td>";
        html_str += "<td>";
        html_str += "<select onchange=\"change_chain_2g(" + node.id + ")\" id=\"ch_2g_" + node.id + "\"></select>";
        html_str += "<select onchange=\"change_bw_2g(" + node.id + ")\" id=\"bw_2g_" + node.id + "\"></select>";
        html_str += "</td>";
        html_str += "<td>";
        html_str += "<select onchange=\"change_chain_5g( " + node.id + ")\" id=\"ch_5g_" + node.id + "\"></select>";
        html_str += "<select onchange=\"change_bw_5g(" + node.id + ")\" id=\"bw_5g_" + node.id + "\"></select>";
        html_str += "</td></tr>";

        //$("#aptable").append(html_str);
        $("#aptable").html(html_str);
        $("#role_" + node.id).append(new Option("None", "none"));
        $("#role_" + node.id).append(new Option("MP", "mp"));
        $("#role_" + node.id).append(new Option("GW", "gw"));
        $("#role_" + node.id).append(new Option("STA_2G", "sta_2g"));
        $("#role_" + node.id).append(new Option("STA_5G", "sta_5g"));
        $("#role_" + node.id).val(node.role);

        $("#plc_" + node.id).append(new Option("No PLC", "no_plc"));
        $("#plc_" + node.id).append(new Option("MIMO PLC", "mimo_plc"));
        $("#plc_" + node.id).val(node.plc);

        $("#ch_2g_" + node.id).append(new Option("1x1", "1x1"));
        $("#ch_2g_" + node.id).append(new Option("2x2", "2x2"));
        $("#ch_2g_" + node.id).val(node.chain_2g);

        $("#bw_2g_" + node.id).append(new Option("20MHz", "bw20"));
        $("#bw_2g_" + node.id).append(new Option("40MHz", "bw40"));
        $("#bw_2g_" + node.id).val(node.bw_2g);

        $("#bw_5g_" + node.id).append(new Option("20MHz", "bw20"));
        $("#bw_5g_" + node.id).append(new Option("40MHz", "bw40"));
        $("#bw_5g_" + node.id).append(new Option("80MHz", "bw80"));
        $("#bw_5g_" + node.id).val(node.bw_5g);

        $("#ch_5g_" + node.id).append(new Option("1x1", "1x1"));
        $("#ch_5g_" + node.id).append(new Option("2x2", "2x2"));
        $("#ch_5g_" + node.id).append(new Option("3x3", "3x3"));
        $("#ch_5g_" + node.id).val(node.chain_5g);
        change_role(node.id);
    });
}
