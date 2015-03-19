/*jslint browser: true*/
/*global $, jQuery*/

var nodes = [
    {"id": 1, "ip": "192.168.2.21", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "role": "mp"},
    {"id": 2, "ip": "192.168.2.22", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "role": "gw"},
    {"id": 3, "ip": "192.168.2.23", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "role": "mp"},
    {"id": 4, "ip": "192.168.2.24", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "role": "mp"},
    {"id": 5, "ip": "192.168.2.25", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "role": "sta_5g"},
    {"id": 6, "ip": "192.168.2.26", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "1x1", "role": "mp"},
    {"id": 7, "ip": "192.168.2.27", "bw_2g" : "bw40", "bw_5g" : "bw80", "chain_2g" : "2x2", "chain_5g" : "3x3", "role": "mp"}
];

function get_test(src, dest, chain_src, chain_dst, band, bw) {
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

function change_role(id) {
    "use strict";
    nodes[id - 1].role = $("#role_" + id).val();
}

function change_bw_2g(id) {
    "use strict";
    nodes[id - 1].bw_2g = $("#bw_2g_" + id).val();
}

function change_bw_5g(id) {
    "use strict";
    nodes[id - 1].bw_5g = $("#bw_5g_" + id).val();
}

function change_chain_5g(id) {
    "use strict";
    nodes[id - 1].chain_5g = $("#ch_5g_" + id).val();
}

function change_chain_2g(id) {
    "use strict";
    nodes[id - 1].chain_2g = $("#ch_2g_" + id).val();
}

function change_chain_5g(id) {
    "use strict";
    nodes[id - 1].chain_5g = $("#ch_5g_" + id).val();
}

function get_src_dst_pairs() {
    "use strict";
    var srcs = [];
    var dests = [];
    var pairs = [];

    nodes.forEach(function (node) {
        if (node.role === "sta_2g" || node.role === "sta_5g") {
            dests.push(node.id - 1);
        } else if (node.role === "gw") {
            srcs.push(node.id - 1);
        }
    });

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
    nodes.forEach(function (node) {
        if (node.role === "mp") {
            mps.push(node.id - 1);
        }
    });
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

        sub_perms.forEach(function (perm) {
            perm_list.push(elem.concat(perm));
        });
    }
    return perm_list;
}

function hop_calc_tput(hop) {
    "use strict";
    var src_node = nodes[hop.src];
    var dest_node = nodes[hop.dest];
    var dat = 0;

    var bw = "bw20";

    if (hop.band === "2g") {
        if (src_node.bw_2g < dest_node.bw_2g) {
            bw = src_node.bw_2g;
        } else {
            bw = dest_node.bw_2g;
        }
        dat = get_test(src_node.ip, dest_node.ip, src_node.chain_2g, dest_node.chain_2g, hop.band, bw);
    } else {
        if (src_node.bw_5g < dest_node.bw_5g) {
            bw = src_node.bw_5g;
        } else {
            bw = dest_node.bw_5g;
        }
        dat = get_test(src_node.ip, dest_node.ip, src_node.chain_5g, dest_node.chain_5g, hop.band, bw);
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

function path_to_str(path) {
    "use strict";
    var res_str = "";
    path.forEach(function (hop) {
        //res_str += " (" + nodes[hop.src].id + " -> " + nodes[hop.dest].id + " , " + hop.tput + ")";
        res_str += " (" + nodes[hop.src].id + " -> " + nodes[hop.dest].id + " , " + Math.round(hop.tput * 100) / 100 + ")";
    });
    return res_str;
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
        var hops = [];
        var current_node = src_idx;
        route.forEach(function (node) {
            var hop = {"src" : current_node, "dest" : node, "tput" : 0, "band" : "5g"};
            hop_calc_tput(hop);
            hops.push(hop);
            current_node = node;
        });

        var hop = {"src" : current_node, "dest" : dest_idx, "tput": 0, "band" : "2g"};
        if (nodes[dest_idx].role === 'sta_5g') {
            hop.band = "5g";
            hop.bw = "bw80";
        }
        hop_calc_tput(hop);
        hops.push(hop);

        paths.push(hops);
    });

    paths.forEach(function (path) {
        costs.push(calculate_path_cost(path));
    });

    var min_idx = costs.indexOf(Math.min.apply(Math, costs));

    var str = JSON.stringify(paths, null, 2);

    //console.log(paths);
    return paths[min_idx];
}

function calculate_routes() {
    "use strict";
    var pairs = get_src_dst_pairs();
    var mps = get_mps();

    var disp_str = "";

    pairs.forEach(function (pair) {
        var best = find_best_route(pair.src, pair.dest, mps);
        disp_str += nodes[pair.src].id + " -> " + nodes[pair.dest].id + " ==> " + path_to_str(best) + "\n";
        console.log(best);
    });
    $("#result").val(disp_str);
}

function test() {
    "use strict";
    nodes.forEach(function (node) {
        var html_str = "<tr><td>" + node.id +  "</td><td><select onchange=\"change_role(" + node.id + ")\" id=\"role_" + node.id + "\"></select></td>";
        html_str +=  "<td>";
        html_str += "<select onchange=\"change_chain_2g(" + node.id + ")\" id=\"ch_2g_" + node.id + "\"></select>";
        html_str += "<select onchange=\"change_bw_2g(" + node.id + ")\" id=\"bw_2g_" + node.id + "\"></select>";
        html_str +=  "</td>";
        html_str +=  "<td>";
        html_str += "<select onchange=\"change_chain_5g( " + node.id + ")\" id=\"ch_5g_" + node.id + "\"></select>";
        html_str += "<select onchange=\"change_bw_5g(" + node.id + ")\" id=\"bw_5g_" + node.id + "\"></select>";
        html_str += "</td></tr>";

        $("#aptable").append(html_str);
        $("#role_" + node.id).append(new Option("None", "none"));
        $("#role_" + node.id).append(new Option("MP", "mp"));
        $("#role_" + node.id).append(new Option("GW", "gw"));
        $("#role_" + node.id).append(new Option("STA_2G", "sta_2g"));
        $("#role_" + node.id).append(new Option("STA_5G", "sta_5g"));
        $("#role_" + node.id).val(node.role);

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
    });
}
