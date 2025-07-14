from core.eval.test_lef import test_queries_lef
from core.eval.test_tlef import test_queries_tlef
from core.eval.test_lib import test_queries_lib
from core.eval.test_graph import test_design

test_queries = test_queries_lib + test_queries_tlef + test_queries_lef

test_queries_byview = {
    'lib': test_queries_lib,
    'tlef': test_queries_tlef,
    'lef': test_queries_lef
}

def count_sql_statistics(queries):
    stats = {
        "Total #": len(queries),
        "# of JOIN": 0,
        "# of ORDER BY": 0,
        "# of WHERE": 0,
        "# of GROUP BY": 0,
        "# of Aggregation Functions": 0,
        "# of Subqueries": 0,
        "Total Length": 0,
        "Maximum Length": 0
    }
    
    agg_functions = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']
        
    for query in queries:
       
        
        # Convert to uppercase for case-insensitive matching
        upper_query = query["ground_truth"][0].upper()
        
        stats["# of JOIN"] += upper_query.count(" JOIN ")
        stats["# of ORDER BY"] += upper_query.count("ORDER BY")
        stats["# of WHERE"] += upper_query.count("WHERE")
        stats["# of GROUP BY"] += upper_query.count("GROUP BY")
        stats["# of Subqueries"] += upper_query.count("(SELECT")
        
        # Count aggregation functions
        stats["# of Aggregation Functions"] += sum(upper_query.count(func) for func in agg_functions)
        
        # Update length statistics
        query_length = len(query["ground_truth"][0])
        stats["Total Length"] += query_length
        stats["Maximum Length"] = max(stats["Maximum Length"], query_length)

    # Calculate average length
    stats["Average Length"] = stats["Total Length"] // stats["Total #"]
    
    return stats


def count_cypher_stats(queries):
    stats = {
        "Total #": len(queries),
        "# of WHERE": 0,
        "# of WITH": 0,
        "# of ORDER BY": 0,
        "# of RETURN": 0,
        "# of Aggregation Functions": 0,
        "# of Pattern Comprehensions": 0,
        "# of Implicit Groupings": 0,
        "# of Subqueries": 0,
        "Total Length": 0,
        "Maximum Length": 0
    }
    
    agg_functions = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'COLLECT']
    
    for query in queries:
        # Convert to uppercase for case-insensitive matching
        upper_query = query["ground_truth"][0].upper()
        
        stats["# of WHERE"] += upper_query.count("WHERE")
        stats["# of WITH"] += upper_query.count("WITH")
        stats["# of ORDER BY"] += upper_query.count("ORDER BY")
        stats["# of RETURN"] += upper_query.count("RETURN")
        
        # Count pattern comprehensions
        stats["# of Pattern Comprehensions"] += upper_query.count("[(")
        
        # Count aggregation functions
        agg_count = sum(upper_query.count(func) for func in agg_functions)
        stats["# of Aggregation Functions"] += agg_count
        stats["# of Implicit Groupings"] += agg_count > 0  
        stats["# of Subqueries"] += upper_query.count("CALL {") + upper_query.count("WITH") * upper_query.count("MATCH")

        # Update length statistics
        query_length = len(query["ground_truth"][0])
        stats["Total Length"] += query_length
        stats["Maximum Length"] = max(stats["Maximum Length"], query_length)

    # Calculate average length
    stats["Average Length"] = stats["Total Length"] // stats["Total #"]
    
    return stats


__all__ = [
    'count_sql_statistics',
    'count_cypher_stats'
]


def main():
    # print statistics of the evaluation set 
    print("Number of LEF Queries: ", len(test_queries_lef))
    print("Number of TechLEF Queries: ", len(test_queries_tlef))
    print("Number of LIB Queries: ", len(test_queries_lib))

    lef_stats = count_sql_statistics(test_queries_lef)
    tlef_stats = count_sql_statistics(test_queries_tlef)
    lib_stats = count_sql_statistics(test_queries_lib)
    all_stats = count_sql_statistics(test_queries)

    print("-----------LEF Stats --------------")
    for key in lef_stats.keys():
        print(key, ": ", lef_stats[key])
    
    print("-----------TechLEF Stats --------------")
    for key in tlef_stats.keys():
        print(key, ": ", tlef_stats[key])

    print("-----------LIB Stats --------------")
    for key in lib_stats.keys():
        print(key, ": ", lib_stats[key])

    print("-----------Total Stats --------------")
    for key in all_stats.keys():
        print(key, ": ", all_stats[key])
        
    cypher_stats = count_cypher_stats(test_design)
    print("-----------Cypher Stats --------------")
    for key in cypher_stats.keys():
        print(key, ": ", cypher_stats[key])


if __name__ == '__main__':
    main()
    