# -*- coding: utf-8 -*-
from typing import List, Optional


class BasicTree:
    def __init__(self, name: Optional[str] = None):
        """
        > The `__init__` function is called when a new instance of the class is created

        Args:
            name (Optional[str]): The name of the node.
        """
        self.name: Optional[str] = name
        self.children: List["BasicTree"] = []
        self.parent: Optional["BasicTree"] = None

    def set_parent(self, parent: "BasicTree") -> None:
        """
        "Set the parent of this node to the given node."

        The first line is a docstring. It's a string that describes what the
        function does. It's good practice to include docstrings in your
        functions

        Args:
            parent ("BasicTree"): The parent of the node.
        """
        self.parent = parent

    def set_child(self, child: "BasicTree") -> None:
        """
        "Add a child to the list of children."

        The first line is a comment. It's not necessary, but it's good practice
        to include a comment at the top of each function that describes what the
        function does

        Args:
            child ("BasicTree"): The child node to be added to the current node.
        """
        self.children.append(child)

    @property
    def num_children(self) -> int:
        """
        "Return the number of children of this node."

        The first line of the function is a docstring. It's a string that
        describes what the function does. It's good practice to include a
        docstring with every function you write

        Returns:
            The number of children in the tree.
        """
        return len(self.children)

    def get_tree(self, key: str) -> "BasicTree":
        """
        If the current node is the node we're looking for, return it. Otherwise,
        if the current node has children, search through them. If we find the
        node we're looking for, return it. Otherwise, return an empty tree

        Args:
            key (str): The name of the tree you want to find.

        Returns:
            A tree with the name of the node that matches the key.
        """
        if self.name == key:
            return self

        elif self.num_children > 0:
            for child in self.children:
                val = child.get_tree(key)
                if val.name is not None:
                    return val

        return BasicTree()


def test():
    """
    > The function `test()` creates a tree with the following structure:
    >
    >
    """
    # tree_dict: Dict[str, Any] = {"a": {"b": "c", "d": {"e": "f"}, "g": {"h": "i"}}}

    a_tree: BasicTree = BasicTree(name="a")
    b_tree: BasicTree = BasicTree(name="b")
    c_tree: BasicTree = BasicTree(name="c")
    d_tree: BasicTree = BasicTree(name="d")
    e_tree: BasicTree = BasicTree(name="e")
    f_tree: BasicTree = BasicTree(name="f")
    g_tree: BasicTree = BasicTree(name="g")
    h_tree: BasicTree = BasicTree(name="h")
    i_tree: BasicTree = BasicTree(name="i")

    a_tree.set_child(b_tree)
    a_tree.set_child(d_tree)
    a_tree.set_child(g_tree)
    b_tree.set_child(c_tree)
    d_tree.set_child(e_tree)
    g_tree.set_child(h_tree)
    e_tree.set_child(f_tree)
    h_tree.set_child(i_tree)

    test_res = []
    for alp in "abcdefghi":
        test_res.append(alp == a_tree.get_tree(alp).name)

    if not all(test_res):
        raise AssertionError(f"all of test must be True. But {test_res}")

    print("Test has be run successfully.")


if __name__ == "__main__":
    test()
