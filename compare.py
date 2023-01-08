import argparse
import ast
import re


class FileOptimizer(ast.NodeTransformer):

    def __init__(self):
        self._arg_count = 0
        self.var_dict = {}
        self._var_count = 0
        self.func_dict = {}
        self._func_count = 0
        self.asfunc_dict = {}
        self._asfunc_count = 0
        self.class_dict = {}
        self._class_count = 0

    def visit_arg(self, node):
        node.arg = "arg_{}".format(self._arg_count)
        self._arg_count += 1
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        if node.id not in self.var_dict:
            self.var_dict[node.id] = "var_{}".format(self._var_count)
        node.id = self.var_dict[node.id]
        self._var_count += 1
        self.generic_visit(node)
        return node

    def visit_Module(self, node: ast.Module):
        ast.get_docstring(node, clean=False)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        ast.get_docstring(node, clean=True)
        if node.name not in self.func_dict:
            self.func_dict[node.name] = "func_{}".format(self._func_count)
        node.name = self.func_dict[node.name]
        self._func_count += 1
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        ast.get_docstring(node, clean=True)
        if node.name not in self.asfunc_dict:
            self.asfunc_dict[node.name] = "async_func_{}".format(self._asfunc_count)
        node.name = self.asfunc_dict[node.name]
        self._asfunc_count += 1
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        ast.get_docstring(node, clean=True)
        if node.name not in self.class_dict:
            self.class_dict[node.name] = "class_{}".format(self._class_count)
        node.name = self.class_dict[node.name]
        self._class_count += 1
        self.generic_visit(node)
        return node


class PlagiatScanner():

    def __init__(self, code1=None, code2=None):
        self.code1 = code1
        self.code2 = code2

    def compute_Levenshtein_distance(self):
        len1, len2 = len(self.code1), len(self.code2)
        if len1 > len2:
            self.code1, self.code2 = self.code2, self.code1
            len1, len2 = len2, len1

        current_row = range(len1 + 1)
        for i in range(1, len2 + 1):
            previous_row, current_row = current_row, [i] + [0] * len1
            for j in range(1, len1 + 1):
                add = previous_row[j] + 1
                delete = current_row[j - 1] + 1
                change = previous_row[j - 1]
                if self.code1[j - 1] != self.code2[i - 1]:
                    change += 1
                current_row[j] = min(add, delete, change)

        return current_row[len1]




def analize_file_types(file1, file2, index):
    search1 = re.search(r'.py', file1, re.M | re.I)
    search2 = re.search(r'.py', file2, re.M | re.I)
    if not search1:
        print(f"Файл {file1} (строка {index + 1}), "
              f"предложенный для сравнения, не является python-файлом")
    if not search2:
        print(f"Файл {file2} (строка {index + 1}), "
              f"предложенный для сравнения, не является python-файлом")



def main():
    parser = argparse.ArgumentParser(description="Antiplagiat tool")
    parser.add_argument(
        "--input", default="input.txt",
        help="Path to the file with pairs of files to compare",
    )
    parser.add_argument(
        "--scores", default="scores.txt",
        help="Path to the result file",
    )
    args = parser.parse_args()

    with open(args.input, mode="r", encoding="utf-8") as file:
        pairs = file.read().rstrip().split('\n')

    score_list = []

    for i, pair in enumerate(pairs):
        pair = re.sub("\s\s+", " ", pair)

        try:
            file1 = pair.split(' ')[0]
            file2 = pair.split(' ')[1]
        except Exception:
            print(f"line {i + 1} in file"
                  f"{args.input} contain less then 2 files")
            raise SystemExit

        analize_file_types(file1, file2, i)

        with open(file1, mode="r", encoding="utf-8") as f:
            code1_before = f.read()
        with open(file2, mode="r", encoding="utf-8") as f:
            code2_before = f.read()

        tree1_before_opt = ast.parse(code1_before)
        tree2_before_opt = ast.parse(code2_before)

        optimizer1 = FileOptimizer()
        optimizer2 = FileOptimizer()

        tree1_after_opt = optimizer1.visit(tree1_before_opt)
        tree2_after_opt = optimizer2.visit(tree2_before_opt)

        code1_after = ast.unparse(tree1_after_opt)
        code2_after = ast.unparse(tree2_after_opt)

        plagiat_scanner = PlagiatScanner(code1_after, code2_after)

        try:
            score_list.append(
                round(
                    plagiat_scanner.compute_Levenshtein_distance()
                    / ((len(code1_after) + len(code2_after)) / 2), 4
                )
            )
        except Exception:
            score_list.append(0)

    with open(args.scores, mode="w", encoding="utf-8") as file:
        file.write('\n'.join(str(x) for x in score_list))


if __name__ == "__main__":
    main()