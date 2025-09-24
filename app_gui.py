# app_gui.py (versão final com associação de perfis a tipos)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import json
import re
import pandas as pd
import ezdxf

from src.dxf_analyzer import analyze_dxf_file
from src.excel_reporter import create_excel_report

PROFILES_FILE = 'profiles.json'

class ProfileManagerWindow:
    def __init__(self, root):
        self.window = tk.Toplevel(root)
        self.window.title("Gerenciador de Perfis")
        self.window.geometry("600x600")
        self.window.transient(root)
        self.window.grab_set()

        # --- MUDANÇA: profiles agora é um dicionário ---
        self.profiles = self.load_profiles()

        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill="both", expand=True)
        
        add_frame = ttk.LabelFrame(frame, text="Adicionar Novo Perfil", padding="10")
        add_frame.pack(fill="x", pady=5)
        
        desc_frame = ttk.Frame(add_frame)
        desc_frame.pack(fill='x', pady=2)
        ttk.Label(desc_frame, text="Descrição (Ex: U, TUBO):", width=20).pack(side="left")
        self.desc_entry = ttk.Entry(desc_frame)
        self.desc_entry.pack(side="left", fill="x", expand=True)
        
        self.measures_frame = ttk.Frame(add_frame)
        self.measures_frame.pack(fill='x', pady=2)
        self.measure_vars = []
        self.add_measure_field()
        
        ttk.Button(add_frame, text="+ Adicionar Medida", command=self.add_measure_field).pack(pady=5)
        
        thick_frame = ttk.Frame(add_frame)
        thick_frame.pack(fill='x', pady=2)
        ttk.Label(thick_frame, text="Espessura (mm):", width=20).pack(side="left")
        self.thick_entry = ttk.Entry(thick_frame)
        self.thick_entry.pack(side="left", fill="x", expand=True)

        # --- NOVO: Checkboxes para associar tipos ---
        types_frame = ttk.LabelFrame(add_frame, text="Associar aos Tipos", padding="10")
        types_frame.pack(fill='x', pady=(10, 5))

        self.is_diagonal = tk.BooleanVar()
        self.is_montante = tk.BooleanVar()
        self.is_banzo = tk.BooleanVar()
        
        ttk.Checkbutton(types_frame, text="DIAGONAL", variable=self.is_diagonal).pack(side="left", padx=5)
        ttk.Checkbutton(types_frame, text="MONTANTE", variable=self.is_montante).pack(side="left", padx=5)
        ttk.Checkbutton(types_frame, text="BANZO", variable=self.is_banzo).pack(side="left", padx=5)
        
        ttk.Button(add_frame, text="Adicionar Perfil à Lista", command=self.add_profile).pack(pady=10)

        # Seção da Lista de Perfis
        list_frame = ttk.LabelFrame(frame, text="Perfis Cadastrados", padding="10")
        list_frame.pack(fill="both", expand=True, pady=5)
        
        self.profiles_listbox = tk.Listbox(list_frame)
        self.profiles_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.profiles_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.profiles_listbox.config(yscrollcommand=scrollbar.set)
        self.populate_listbox()

        action_frame = ttk.Frame(frame, padding="5")
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Remover Selecionado", command=self.remove_profile).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(action_frame, text="Gerar DXF de Template", command=self.generate_template_dxf).pack(side="left", expand=True, fill="x", padx=2)

    def add_measure_field(self):
        # (Sem alterações aqui)
        measure_count = len(self.measure_vars) + 1; frame = ttk.Frame(self.measures_frame); frame.pack(fill='x', pady=1)
        ttk.Label(frame, text=f"Medida {measure_count} (mm):", width=20).pack(side="left")
        var = tk.StringVar(); self.measure_vars.append(var); entry = ttk.Entry(frame, textvariable=var); entry.pack(side="left", fill="x", expand=True)
        
    def reset_fields(self):
        # (Adicionado reset dos checkboxes)
        self.desc_entry.delete(0, tk.END); self.thick_entry.delete(0, tk.END)
        for widget in self.measures_frame.winfo_children(): widget.destroy()
        self.measure_vars.clear(); self.add_measure_field()
        self.is_diagonal.set(False); self.is_montante.set(False); self.is_banzo.set(False)

    def normalize_name_part(self, part):
        # (Sem alterações aqui)
        part = str(part).strip().upper(); part = re.sub(r'[\s,./\\*]', '_', part); part = part.replace('.', 'X'); return re.sub(r'__+', '_', part)

    def add_profile(self):
        # (Lógica atualizada para usar dicionário e checkboxes)
        desc = self.desc_entry.get(); thickness = self.thick_entry.get()
        measures = [var.get() for var in self.measure_vars if var.get().strip()]
        if not desc or not measures or not thickness: messagebox.showerror("Erro", "Descrição, Medida e Espessura são obrigatórios.", parent=self.window); return
        try: [float(m.replace(',', '.')) for m in measures]; float(thickness.replace(',', '.'))
        except ValueError: messagebox.showerror("Erro", "Medida e Espessura devem ser números.", parent=self.window); return

        selected_types = []
        if self.is_diagonal.get(): selected_types.append("DIAGONAL")
        if self.is_montante.get(): selected_types.append("MONTANTE")
        if self.is_banzo.get(): selected_types.append("BANZO")

        if not selected_types:
            messagebox.showerror("Erro", "Associe o perfil a pelo menos um tipo (DIAGONAL, MONTANTE ou BANZO).", parent=self.window)
            return
            
        name_parts = [self.normalize_name_part(p) for p in [desc] + measures + [thickness]]
        final_profile_name = "_".join(name_parts)

        if final_profile_name in self.profiles: messagebox.showwarning("Aviso", "Este perfil já está cadastrado.", parent=self.window)
        else:
            self.profiles[final_profile_name] = selected_types
            self.save_profiles(); self.populate_listbox(); self.reset_fields()

    def load_profiles(self):
        # (Lógica atualizada para carregar um dicionário)
        if not os.path.exists(PROFILES_FILE): return {}
        try:
            with open(PROFILES_FILE, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (IOError, json.JSONDecodeError): return {}
    
    def save_profiles(self):
        # (Lógica atualizada para salvar um dicionário)
        try:
            with open(PROFILES_FILE, 'w') as f: json.dump(self.profiles, f, indent=4, sort_keys=True)
        except IOError: messagebox.showerror("Erro", "Não foi possível salvar a lista de perfis.", parent=self.window)
    
    def populate_listbox(self):
        # (Lógica atualizada para exibir os tipos associados)
        self.profiles_listbox.delete(0, tk.END)
        for name, types in sorted(self.profiles.items()):
            display_text = f"{name} ({', '.join(types)})"
            self.profiles_listbox.insert(tk.END, display_text)

    def remove_profile(self):
        # (Lógica atualizada para extrair o nome do perfil da lista)
        selected_indices = self.profiles_listbox.curselection()
        if not selected_indices: messagebox.showwarning("Aviso", "Selecione um perfil para remover.", parent=self.window); return
        
        display_text = self.profiles_listbox.get(selected_indices[0])
        profile_name = display_text.split(' ')[0] # Extrai apenas o nome

        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja remover o perfil '{profile_name}'?", parent=self.window):
            if profile_name in self.profiles:
                del self.profiles[profile_name]
                self.save_profiles(); self.populate_listbox()

    def generate_template_dxf(self):
        # (Lógica atualizada para criar apenas as layers associadas)
        if not self.profiles: messagebox.showwarning("Aviso", "Não há perfis cadastrados.", parent=self.window); return
        save_path = filedialog.asksaveasfilename(title="Salvar Template DXF", defaultextension=".dxf", filetypes=[("Arquivos DXF", "*.dxf")])
        if not save_path: return
        try:
            doc = ezdxf.new()
            for profile_name, types in self.profiles.items():
                if "DIAGONAL" in types: doc.layers.new(f'DIAGONAL_{profile_name}', dxfattribs={'color': 1})
                if "MONTANTE" in types: doc.layers.new(f'MONTANTE_{profile_name}', dxfattribs={'color': 3})
                if "BANZO" in types: doc.layers.new(f'BANZO_{profile_name}', dxfattribs={'color': 5})
            
            doc.saveas(save_path)
            messagebox.showinfo("Sucesso", f"Template DXF salvo com sucesso em:\n{save_path}", parent=self.window)
        except Exception as e: messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar o arquivo DXF:\n{e}", parent=self.window)

# --- Classe Principal da Aplicação (sem alterações) ---
class App:
    def __init__(self, root):
        self.root = root; self.root.title("Analisador de Treliças DXF"); self.root.geometry("850x600")
        menubar = tk.Menu(root); root.config(menu=menubar)
        options_menu = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label="Opções", menu=options_menu)
        options_menu.add_command(label="Gerenciar Perfis...", command=self.open_profile_manager)
        self.selected_files = []; self.selected_files_label_text = tk.StringVar(); self.selected_files_label_text.set("Nenhum arquivo selecionado")
        self.status_text = tk.StringVar(); self.status_text.set("Pronto."); self.progress_var = tk.DoubleVar()
        main_frame = ttk.Frame(root, padding="10"); main_frame.pack(fill="both", expand=True)
        input_frame = ttk.LabelFrame(main_frame, text="1. Seleção de Arquivos", padding="10"); input_frame.pack(fill="x", pady=5)
        ttk.Button(input_frame, text="Selecionar Arquivo(s) DXF", command=self.select_files).pack(side="left", padx=(0, 10))
        ttk.Label(input_frame, textvariable=self.selected_files_label_text).pack(side="left", fill="x", expand=True)
        action_frame = ttk.Frame(main_frame, padding="10"); action_frame.pack(fill="x")
        self.analyze_button = ttk.Button(action_frame, text="2. Analisar Arquivos e Gerar Relatório", command=self.start_analysis_thread)
        self.analyze_button.pack(pady=10)
        results_frame = ttk.LabelFrame(main_frame, text="3. Resumo dos Resultados", padding="10"); results_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(results_frame, columns=("Tipo", "Perfil", "Qtd", "Comprimento", "Barras"), show="headings")
        self.tree.heading("Tipo", text="Tipo"); self.tree.column("Tipo", width=120)
        self.tree.heading("Perfil", text="Perfil"); self.tree.column("Perfil", width=200)
        self.tree.heading("Qtd", text="Qtd. Peças"); self.tree.column("Qtd", width=100, anchor='center')
        self.tree.heading("Comprimento", text="Comprimento Total (mm)"); self.tree.column("Comprimento", width=180, anchor='e')
        self.tree.heading("Barras", text="Barras de 6m"); self.tree.column("Barras", width=100, anchor='center')
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=vsb.set); vsb.pack(side='right', fill='y')
        self.tree.pack(fill="both", expand=True)
        status_frame = ttk.Frame(main_frame, padding=(10, 5)); status_frame.pack(fill="x")
        ttk.Label(status_frame, textvariable=self.status_text).pack(side="left")
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(10, 0))
    def open_profile_manager(self): ProfileManagerWindow(self.root)
    def select_files(self):
        files = filedialog.askopenfilenames(title="Selecione", filetypes=[("Arquivos DXF", "*.dxf")])
        if files: self.selected_files = files; count = len(files); self.selected_files_label_text.set(os.path.basename(files[0]) if count == 1 else f"{count} arquivo(s) selecionado(s)"); self.status_text.set(f"{count} arquivo(s) pronto(s) para análise.")
    def start_analysis_thread(self):
        if not self.selected_files: messagebox.showwarning("Aviso", "Selecione um arquivo."); return
        self.analyze_button.config(state="disabled"); [self.tree.delete(i) for i in self.tree.get_children()]
        thread = threading.Thread(target=self.run_analysis, daemon=True); thread.start()
    def run_analysis(self):
        try:
            all_results = []
            for i, filepath in enumerate(self.selected_files):
                filename = os.path.basename(filepath); progress = (i / len(self.selected_files)) * 100
                self.root.after(0, self.progress_var.set, progress); self.root.after(0, self.status_text.set, f"Processando: {filename} ({i+1}/{len(self.selected_files)})")
                analysis_data = analyze_dxf_file(filepath)
                if analysis_data:
                    summary_df = create_excel_report(analysis_data, filename, "reports")
                    if summary_df is not None: all_results.append(summary_df)
            if all_results:
                final_summary = pd.concat(all_results).groupby(['Tipo', 'Perfil']).sum().reset_index()
                self.root.after(0, self.populate_results_tree, final_summary)
        except Exception as e: self.root.after(0, messagebox.showerror, "Erro Durante a Análise", f"Ocorreu um erro inesperado:\n\n{e}")
        finally: self.root.after(0, self.analysis_complete)
    def populate_results_tree(self, summary_df):
        for index, row in summary_df.iterrows(): self.tree.insert("", "end", values=(row["Tipo"], row["Perfil"], row["Quantidade de Peças"], f'{row["Comprimento Total (mm)"]:.2f}', row["Barras de 6m Necessárias"]))
    def analysis_complete(self):
        self.progress_var.set(100); self.status_text.set("Análise concluída! Relatórios salvos na pasta 'reports'.")
        self.analyze_button.config(state="normal")
        if self.status_text.get().startswith("Análise concluída"): messagebox.showinfo("Sucesso", "Processo concluído com sucesso!")
        self.progress_var.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()