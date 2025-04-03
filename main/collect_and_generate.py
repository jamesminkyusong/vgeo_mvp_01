import collect
import generate
import pandas as pd

def main():
    selected_scenarios_df, cluster_info_df, output_path= collect.main()
    generate.main(selected_scenarios_df, cluster_info_df, output_path)

if __name__ == "__main__":
    main()