# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Inode:
    """Representa un inodo en el sistema de archivos."""
    name: str
    is_directory: bool
    size: int = 0
    content: str = ""
    permissions: str = "rw-r--r--"
    owner: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    children: Dict[str, 'Inode'] = field(default_factory=dict)


class FileSystem:
    """Sistema de archivos básico con estructura de directorios."""

    def __init__(self, capacity: int = 1000):
        """Inicializa el sistema de archivos.

        Args:
            capacity (int): Capacidad total del sistema de archivos.
        """
        self.capacity = capacity
        self.used = 0
        self.root = Inode("/", is_directory=True)
        self.current_dir = self.root

    def _resolve_path(self, path: str) -> Optional[Inode]:
        """Resuelve una ruta absoluta o relativa a un inodo.

        Args:
            path (str): Ruta del archivo o directorio.

        Returns:
            Optional[Inode]: Inodo encontrado o None.
        """
        if path == "/":
            return self.root

        parts = [p for p in path.split("/") if p]
        current = self.root if path.startswith("/") else self.current_dir

        for part in parts:
            if part == "..":
                if current != self.root:
                    current = self._get_parent(current)
            elif part == ".":
                continue
            elif current.is_directory and part in current.children:
                current = current.children[part]
            else:
                return None

        return current

    def _get_parent(self, node: Inode) -> Inode:
        """Obtiene el padre de un inodo."""
        if node == self.root:
            return self.root

        def search(current: Inode, target: Inode) -> Optional[Inode]:
            if not current.is_directory:
                return None
            for child in current.children.values():
                if child == target:
                    return current
                result = search(child, target)
                if result:
                    return result
            return None

        parent = search(self.root, node)
        return parent if parent else self.root

    def mkdir(self, path: str, pid: int = 0) -> bool:
        """Crea un directorio.

        Args:
            path (str): Ruta del directorio.
            pid (int): PID del proceso creador.

        Returns:
            bool: True si creado exitosamente.
        """
        if self._resolve_path(path):
            logging.warning(f"[FS] Directorio ya existe: {path}")
            return False

        parent_path = "/".join(path.split("/")[:-1]) or "/"
        parent = self._resolve_path(parent_path)

        if not parent or not parent.is_directory:
            logging.warning(f"[FS] Padre no encontrado: {parent_path}")
            return False

        name = path.split("/")[-1]
        new_dir = Inode(name, is_directory=True, owner=pid)
        parent.children[name] = new_dir
        logging.info(f"[FS] Directorio creado: {path} por PID={pid}")
        return True

    def create_file(self, path: str, content: str = "", pid: int = 0) -> bool:
        """Crea un archivo.

        Args:
            path (str): Ruta del archivo.
            content (str): Contenido inicial.
            pid (int): PID del proceso creador.

        Returns:
            bool: True si creado exitosamente.
        """
        if self._resolve_path(path):
            logging.warning(f"[FS] Archivo ya existe: {path}")
            return False

        parent_path = "/".join(path.split("/")[:-1]) or "/"
        parent = self._resolve_path(parent_path)

        if not parent or not parent.is_directory:
            logging.warning(f"[FS] Padre no encontrado: {parent_path}")
            return False

        if self.used + len(content) > self.capacity:
            logging.warning(f"[FS] Espacio insuficiente para {path}")
            return False

        name = path.split("/")[-1]
        new_file = Inode(name, is_directory=False, size=len(content), content=content, owner=pid)
        parent.children[name] = new_file
        self.used += len(content)
        logging.info(f"[FS] Archivo creado: {path} ({len(content)} bytes) por PID={pid}")
        return True

    def read_file(self, path: str, pid: int = 0) -> Optional[str]:
        """Lee un archivo.

        Args:
            path (str): Ruta del archivo.
            pid (int): PID del proceso lector.

        Returns:
            Optional[str]: Contenido del archivo o None.
        """
        inode = self._resolve_path(path)
        if not inode or inode.is_directory:
            logging.warning(f"[FS] Archivo no encontrado: {path}")
            return None

        logging.info(f"[FS] Lectura: {path} por PID={pid}")
        return inode.content

    def write_file(self, path: str, content: str, pid: int = 0) -> bool:
        """Escribe en un archivo.

        Args:
            path (str): Ruta del archivo.
            content (str): Nuevo contenido.
            pid (int): PID del proceso escritor.

        Returns:
            bool: True si escrito exitosamente.
        """
        inode = self._resolve_path(path)
        if not inode or inode.is_directory:
            logging.warning(f"[FS] Archivo no encontrado: {path}")
            return False

        new_size = len(content)
        if self.used - inode.size + new_size > self.capacity:
            logging.warning(f"[FS] Espacio insuficiente para escribir {path}")
            return False

        self.used -= inode.size
        inode.content = content
        inode.size = new_size
        self.used += new_size
        logging.info(f"[FS] Escritura: {path} ({new_size} bytes) por PID={pid}")
        return True

    def delete(self, path: str, pid: int = 0) -> bool:
        """Elimina un archivo o directorio.

        Args:
            path (str): Ruta a eliminar.
            pid (int): PID del proceso.

        Returns:
            bool: True si eliminado exitosamente.
        """
        inode = self._resolve_path(path)
        if not inode:
            logging.warning(f"[FS] No encontrado: {path}")
            return False

        parent = self._get_parent(inode)
        if not parent or not parent.is_directory:
            return False

        if inode.is_directory:
            self.used -= self._calculate_size(inode)
        else:
            self.used -= inode.size

        del parent.children[inode.name]
        logging.info(f"[FS] Eliminado: {path} por PID={pid}")
        return True

    def _calculate_size(self, node: Inode) -> int:
        """Calcula el tamaño total de un directorio recursivamente."""
        if not node.is_directory:
            return node.size

        total = 0
        for child in node.children.values():
            total += self._calculate_size(child)
        return total

    def list_dir(self, path: str = ".") -> List[str]:
        """Lista el contenido de un directorio.

        Args:
            path (str): Ruta del directorio.

        Returns:
            List[str]: Lista de nombres.
        """
        inode = self._resolve_path(path)
        if not inode or not inode.is_directory:
            return []

        entries = []
        for name, child in inode.children.items():
            prefix = "d" if child.is_directory else "-"
            entries.append(f"{prefix} {name} ({child.size} bytes)")
        return entries

    def tree(self, path: str = "/") -> str:
        """Genera una representación en árbol del sistema de archivos.

        Args:
            path (str): Ruta raíz para el árbol.

        Returns:
            str: Árbol formateado.
        """
        inode = self._resolve_path(path)
        if not inode:
            return ""

        lines = []
        self._build_tree(inode, "", lines, is_last=True)
        return "\n".join(lines)

    def _build_tree(self, node: Inode, prefix: str, lines: List[str], is_last: bool) -> None:
        """Construye el árbol recursivamente."""
        connector = "└── " if is_last else "├── "
        icon = "[D]" if node.is_directory else "[F]"
        lines.append(f"{prefix}{connector}{icon} {node.name}")

        if node.is_directory:
            children = list(node.children.values())
            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                extension = "    " if is_last else "│   "
                self._build_tree(child, prefix + extension, lines, is_last_child)
