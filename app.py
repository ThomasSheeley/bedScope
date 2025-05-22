from shiny import App, ui, reactive, render
import pandas as pd
from pybedtools import BedTool
import tempfile
import re

# Helper to read BED files
def read_bed(file_path):
    return pd.read_csv(file_path, sep="\t", header=None)

# Helper to convert DataFrame to temporary BED file for pybedtools
def df_to_bedtool(df):
    tmp = tempfile.NamedTemporaryFile(mode="w+t", delete=False)
    df.to_csv(tmp.name, sep="\t", header=False, index=False)
    return BedTool(tmp.name)

app_ui = ui.page_navbar(
    ui.nav_panel("BED File 1",
        ui.layout_columns(
            ui.column(12,
                ui.input_file("bed1", "Upload BED File 1", accept=[".bed", ".tsv"]),
            ),
            ui.column(12,
                ui.output_table("bed1_preview")
            )
        )
    ),
    ui.nav_panel("BED File 2",
        ui.layout_columns(
            ui.column(6,
                ui.input_file("bed2", "Upload BED File 2", accept=[".bed", ".tsv"]),
            ),
            ui.column(6,
                ui.output_table("bed2_preview")
            )
        )
    ),
    ui.nav_panel("Compare BED Files",
        ui.layout_columns(
            ui.column(6,
                ui.input_select("compare_a", "Select BED A", choices=["BED File 1", "BED File 2"]),
                ui.input_select("compare_b", "Select BED B", choices=["BED File 1", "BED File 2"]),
            ),
            ui.column(6,
                ui.navset_tab(
                    ui.nav_panel("Summary", 
                        ui.output_text("intersect_summary")
                    ),
                    ui.nav_panel("Regions", 
                        ui.output_table("intersect_preview")
                    ),
                    ui.nav_panel("Fisher's", 
                        ui.output_text_verbatim("fishers_raw"),  # ← displays raw CLI-like output
                        ui.input_file("genome_file", "Optional: Upload .genome file", accept=[".genome", ".txt", ".tsv"]),
                    )
                )
            )
        )
    ),
    title="bedScope"
)

def server(input, output, session):
    # Reactive values for storing DataFrames
    bed1_data = reactive.value(None)
    bed2_data = reactive.value(None)

    @reactive.effect
    def _update_bed1():
        fileinfo = input.bed1()
        if fileinfo is None:
            bed1_data.set(None)
        else:
            df = read_bed(fileinfo[0]["datapath"])
            bed1_data.set(df)

    @reactive.effect
    def _update_bed2():
        fileinfo = input.bed2()
        if fileinfo is None:
            bed2_data.set(None)
        else:
            df = read_bed(fileinfo[0]["datapath"])
            bed2_data.set(df)

    @render.table
    def bed1_preview():
        df = bed1_data.get()
        return df.head() if df is not None else None

    @render.table
    def bed2_preview():
        df = bed2_data.get()
        return df.head() if df is not None else None

    @reactive.calc
    def intersect_df():
        df_a = bed1_data.get() if input.compare_a() == "BED File 1" else bed2_data.get()
        df_b = bed1_data.get() if input.compare_b() == "BED File 1" else bed2_data.get()

        if df_a is None or df_b is None:
            return None

        bt_a = df_to_bedtool(df_a)
        bt_b = df_to_bedtool(df_b)

        intersect = bt_a.intersect(bt_b, wa=True, u=True)
        return pd.read_csv(intersect.fn, sep="\t", header=None)

    @render.table
    def intersect_preview():
        df = intersect_df()
        return df.head() if df is not None else None
    


    @reactive.calc
    def intersect_stats():
        df_a = bed1_data.get() if input.compare_a() == "BED File 1" else bed2_data.get()
        df_b = bed1_data.get() if input.compare_b() == "BED File 1" else bed2_data.get()

        if df_a is None or df_b is None:
            return "Please upload both BED files."

        bt_a = df_to_bedtool(df_a)
        bt_b = df_to_bedtool(df_b)

        total_a = bt_a.count()
        total_b = bt_b.count()
        overlap_count = bt_a.intersect(bt_b, u=True).count()
        non_overlap_count = bt_a.subtract(bt_b).count()

        return (
            f"Total intervals in BED A: {total_a}\n"
            f"Total intervals in BED B: {total_b}\n"
            f"Overlapping intervals: {overlap_count}\n"
            f"Non-overlapping intervals in A: {non_overlap_count}"
        )

    @render.text
    def intersect_summary():
        return intersect_stats()


    @render.text
    def fishers_raw():
        df_a = bed1_data.get() if input.compare_a() == "BED File 1" else bed2_data.get()
        df_b = bed1_data.get() if input.compare_b() == "BED File 1" else bed2_data.get()

        if df_a is None or df_b is None:
            return "Please upload both BED files."

        bt_a = df_to_bedtool(df_a)
        bt_b = df_to_bedtool(df_b)
        genome_fileinfo = input.genome_file()
        genome_path = genome_fileinfo[0]["datapath"] if genome_fileinfo else None

        try:
            if genome_path:
                bt_a = bt_a.sort(g=genome_path)
                bt_b = bt_b.sort(g=genome_path)
                result = bt_a.fisher(bt_b, g=genome_path)
            else:
                bt_a = bt_a.sort()
                bt_b = bt_b.sort()
                result = bt_a.fisher(bt_b)

            return str(result)

        except Exception as e:
            return f"Error running Fisher's test: {e}"







app = App(app_ui, server)
