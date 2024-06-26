# splitter.py
import ast
import sys
import os
import shutil
import subprocess
from pathlib import Path

class FunctionSplitter(ast.NodeVisitor):
    """
    A class to split functions and classes from a Python script into separate files.

    Attributes:
        script_path (str): Path to the input script.
        output_dir (str): Directory to save the split files.
        functions (list): List of function nodes.
        classes (list): List of class nodes.
        imports (list): List of import nodes.
    """

    def __init__(self, script_path, output_dir=None):
        """
        Initializes the FunctionSplitter with the script path and output directory.

        Args:
            script_path (str): Path to the input script.
            output_dir (str, optional): Directory to save the split files. Defaults to None.
        """
        self.script_path = script_path
        self.script_dir = os.path.splitext(script_path)[0]
        self.output_dir = output_dir if output_dir else os.path.splitext(script_path)[0]
        self.functions = []
        self.classes = []
        self.imports = []

    def visit_Import(self, node):
        """
        Visits import statements and stores them.

        Args:
            node (ast.Import): The import node.
        """
        self.imports.append(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """
        Visits import-from statements and stores them.

        Args:
            node (ast.ImportFrom): The import-from node.
        """
        self.imports.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """
        Visits function definitions and stores them.

        Args:
            node (ast.FunctionDef): The function definition node.
        """
        self.functions.append(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """
        Visits class definitions and stores them.

        Args:
            node (ast.ClassDef): The class definition node.
        """
        self.classes.append(node)
        self.generic_visit(node)

    def split_functions(self):
        """
        Splits functions and classes into separate files and updates the original script.
        """
        try:
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
            os.makedirs(self.output_dir)

            with open(self.script_path, 'r') as file:
                script_code = file.read()

            tree = ast.parse(script_code)
            self.visit(tree)

            for func in self.functions:
                self._create_function_file(func, script_code)

            for cls in self.classes:
                self._create_class_file(cls, script_code)

            self._update_original_script(script_code)
        except Exception as e:
            print(f"Error while splitting functions: {e}", file=sys.stderr)
            sys.exit(1)

    def _get_imports_for_node(self, node):
        """
        Gets the necessary import statements for a given node.

        Args:
            node (ast.AST): The AST node.

        Returns:
            str: The import statements.
        """
        used_imports = []
        for imp in self.imports:
            for alias in imp.names:
                if any(alias.name in ast.dump(n) for n in ast.walk(node)):
                    used_imports.append(ast.get_source_segment(open(self.script_path).read(), imp))
                    break
        return "\n".join(used_imports) + "\n"

    def _create_function_file(self, func, script_code):
        """
        Creates a file for a function.

        Args:
            func (ast.FunctionDef): The function node.
            script_code (str): The original script code.
        """
        func_name = func.name
        func_code = self._get_imports_for_node(func)
        for decorator in func.decorator_list:
            func_code += ast.get_source_segment(script_code, decorator) + "\n"
        func_code += ast.get_source_segment(script_code, func)
        func_file_path = os.path.join(self.output_dir, f"{func_name}.py")

        try:
            with open(func_file_path, 'w') as func_file:
                func_file.write(self._get_imports_for_node(func) + func_code)
        except Exception as e:
            print(f"Error while creating function file {func_name}: {e}", file=sys.stderr)
            sys.exit(1)

    def _create_class_file(self, cls, script_code):
        """
        Creates a file for a class.

        Args:
            cls (ast.ClassDef): The class node.
            script_code (str): The original script code.
        """
        class_name = cls.name
        class_code = self._get_imports_for_node(cls)
        for decorator in cls.decorator_list:
            class_code += ast.get_source_segment(script_code, decorator) + "\n"
        class_code += ast.get_source_segment(script_code, cls)
        class_file_path = os.path.join(self.output_dir, f"{class_name}.py")

        try:
            with open(class_file_path, 'w') as class_file:
                class_file.write(self._get_imports_for_node(cls) + class_code)
        except Exception as e:
            print(f"Error while creating class file {class_name}: {e}", file=sys.stderr)
            sys.exit(1)

    def _update_original_script(self, script_code):
        """
        Updates the original script to import the split functions and classes.

        Args:
            script_code (str): The original script code.
        """
        new_script_code = script_code

        for func in self.functions:
            func_name = func.name
            import_statement = f"from .{func_name} import {func_name}\n"
            new_script_code = new_script_code.replace(ast.get_source_segment(script_code, func), import_statement)

        for cls in self.classes:
            class_name = cls.name
            import_statement = f"from .{class_name} import {class_name}\n"
            new_script_code = new_script_code.replace(ast.get_source_segment(script_code, cls), import_statement)

        try:
            with open(self.script_path, 'w') as file:
                file.write(new_script_code)
        except Exception as e:
            print(f"Error while updating original script: {e}", file=sys.stderr)
            sys.exit(1)

    def _handle_method_attributes(self, method_node):
        """
        Handles attributes of a method.

        Args:
            method_node (ast.FunctionDef): The method node.

        Returns:
            set: A set of attribute names.
        """
        attributes = set()
        for node in ast.walk(method_node):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
                attributes.add(node.attr)
        return attributes

    def _create_method_file(self, class_name, method, script_code):
        """
        Creates a file for a method.

        Args:
            class_name (str): The name of the class.
            method (ast.FunctionDef): The method node.
            script_code (str): The original script code.
        """
        method_name = method.name
        method_code = ast.get_source_segment(script_code, method)
        method_file_path = os.path.join(self.script_dir, f"{class_name}_{method_name}.py")

        attributes = self._handle_method_attributes(method)
        args = ', '.join(['self'] + list(attributes))
        new_method_code = f"def {method_name}({args}):\n"
        for line in method_code.split('\n')[1:]:
            new_method_code += f"    {line}\n"

        with open(method_file_path, 'w') as method_file:
            method_file.write(self._get_imports_code() + new_method_code)

    def _update_class_methods(self, class_node, script_code):
        """
        Updates class methods to call the split methods.

        Args:
            class_node (ast.ClassDef): The class node.
            script_code (str): The original script code.

        Returns:
            str: The updated class code.
        """
        class_name = class_node.name
        new_class_code = ast.get_source_segment(script_code, class_node)

        for method in class_node.body:
            if isinstance(method, ast.FunctionDef):
                self._create_method_file(class_name, method, script_code)
                attributes = self._handle_method_attributes(method)
                args = ', '.join(['self'] + list(attributes))
                call_args = ', '.join([f"self.{attr}" for attr in attributes])
                decorator_code = ""
                for decorator in method.decorator_list:
                    decorator_code += f"    {ast.get_source_segment(script_code, decorator)}\n"
                new_method_code = f"{decorator_code}    def {method.name}({args}):\n        pass\n"
                new_class_code = new_class_code.replace(ast.get_source_segment(script_code, method), new_method_code)

        return new_class_code

    def _get_imports_code(self):
        """
        Gets all import statements from the original script.

        Returns:
            str: The import statements.
        """
        imports_code = ""
        for imp in self.imports:
            imports_code += ast.get_source_segment(open(self.script_path).read(), imp) + "\n"
        return imports_code

    def _is_git_repo(self):
        """
        Checks if the script is in a git repository.

        Returns:
            Path or None: The path to the git repository or None if not found.
        """
        current_path = Path(self.script_path).resolve()
        for parent in [current_path] + list(current_path.parents):
            if (parent / ".git").exists():
                return parent
        return None

    def _create_git_branch(self, branch_name):
        """
        Creates a new git branch.

        Args:
            branch_name (str): The name of the new branch.
        """
        try:
            subprocess.check_call(['git', 'checkout', '-b', branch_name])
        except subprocess.CalledProcessError as e:
            print(f"Error while creating git branch: {e}", file=sys.stderr)
            sys.exit(1)

    def _commit_changes(self, message):
        """
        Commits changes to the git repository.

        Args:
            message (str): The commit message.
        """
        try:
            subprocess.check_call(['git', 'add', '.'])
            subprocess.check_call(['git', 'commit', '-m', message])
        except subprocess.CalledProcessError as e:
            print(f"Error while committing changes: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    import sys
    if len(sys.argv) not in [2, 3]:
        print("Usage: python splitter.py <script_path> [output_dir]")
        sys.exit(1)

    script_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) == 3 else None
    splitter = FunctionSplitter(script_path, output_dir)

    git_repo_path = splitter._is_git_repo()
    if git_repo_path:
        os.chdir(git_repo_path)
        branch_name = "split-functions"
        splitter._create_git_branch(branch_name)
        splitter.split_functions()
        splitter._commit_changes("Split functions and methods into separate files")
        print(f"Changes committed to new branch '{branch_name}'.")
    else:
        print("Not a git repository. Please initialize a git repository first.")
        sys.exit(1)
