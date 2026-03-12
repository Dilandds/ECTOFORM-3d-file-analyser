"""
File format converter for 3D CAD files.
Supports: 3DM → STEP, 3DM → STL, STEP → STL
"""
import logging
import os

logger = logging.getLogger(__name__)


class FileConverter:
    """Handles conversion between 3D file formats."""

    @staticmethod
    def convert_3dm_to_stl(input_path, output_path):
        """Convert 3DM file to STL format."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        from core.rhino3dm_loader import Rhino3dmLoader
        logger.info(f"FileConverter: Converting 3DM → STL: {input_path}")

        mesh = Rhino3dmLoader.load_with_rhino3dm(input_path)
        if mesh is None:
            raise ValueError("Failed to load 3DM file. The file may be empty or contain unsupported geometry.")

        mesh.save(output_path)
        logger.info(f"FileConverter: Successfully saved STL to {output_path}")
        return True

    @staticmethod
    def convert_step_to_stl(input_path, output_path):
        """Convert STEP file to STL format."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        from core.step_loader import StepLoader
        logger.info(f"FileConverter: Converting STEP → STL: {input_path}")

        mesh = StepLoader.load_step(input_path)
        if mesh is None:
            raise ValueError("Failed to load STEP file.")

        mesh.save(output_path)
        logger.info(f"FileConverter: Successfully saved STL to {output_path}")
        return True

    @staticmethod
    def convert_3dm_to_step(input_path, output_path):
        """Convert 3DM file to STEP format using OCP."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        logger.info(f"FileConverter: Converting 3DM → STEP: {input_path}")

        try:
            import rhino3dm
            from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
            from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace
            from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
            from OCP.gp import gp_Pnt, gp_Vec
            from OCP.BRep import BRep_Builder
            from OCP.TopoDS import TopoDS_Compound
            from OCP.Interface import Interface_Static
        except ImportError as e:
            raise ImportError(
                f"Required libraries not available for 3DM → STEP conversion: {e}\n"
                "Install cadquery or OCP (pip install cadquery)"
            )

        model = rhino3dm.File3dm.Read(input_path)
        if model is None:
            raise ValueError("Failed to read 3DM file.")
        if model.Objects is None or len(model.Objects) == 0:
            raise ValueError("3DM file contains no objects.")

        # Build a compound from mesh triangles
        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)

        face_count = 0

        for obj in model.Objects:
            geometry = obj.Geometry
            if geometry is None:
                continue

            # Get mesh from various geometry types
            meshes = []
            if isinstance(geometry, rhino3dm.Mesh):
                meshes.append(geometry)
            elif isinstance(geometry, rhino3dm.Brep):
                for brep_face in geometry.Faces:
                    try:
                        m = brep_face.GetMesh(rhino3dm.MeshType.Render)
                        if m is None:
                            m = brep_face.GetMesh(rhino3dm.MeshType.Any)
                        if m is not None:
                            meshes.append(m)
                    except Exception:
                        continue
            elif isinstance(geometry, rhino3dm.Extrusion):
                try:
                    brep = geometry.ToBrep()
                    if brep:
                        for brep_face in brep.Faces:
                            try:
                                m = brep_face.GetMesh(rhino3dm.MeshType.Render)
                                if m is None:
                                    m = brep_face.GetMesh(rhino3dm.MeshType.Any)
                                if m is not None:
                                    meshes.append(m)
                            except Exception:
                                continue
                except Exception:
                    continue

            # Convert meshes to OCP faces
            for mesh in meshes:
                vertices = mesh.Vertices
                faces = mesh.Faces
                if not vertices or not faces:
                    continue

                sewing = BRepBuilderAPI_Sewing(1e-6)

                for face in faces:
                    try:
                        p0 = gp_Pnt(vertices[face[0]].X, vertices[face[0]].Y, vertices[face[0]].Z)
                        p1 = gp_Pnt(vertices[face[1]].X, vertices[face[1]].Y, vertices[face[1]].Z)
                        p2 = gp_Pnt(vertices[face[2]].X, vertices[face[2]].Y, vertices[face[2]].Z)

                        edge1 = BRepBuilderAPI_MakeEdge(p0, p1).Edge()
                        edge2 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
                        edge3 = BRepBuilderAPI_MakeEdge(p2, p0).Edge()

                        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeWire
                        wire = BRepBuilderAPI_MakeWire(edge1, edge2, edge3).Wire()
                        ocp_face = BRepBuilderAPI_MakeFace(wire).Face()
                        sewing.Add(ocp_face)
                        face_count += 1

                        # Handle quad faces
                        if face[2] != face[3]:
                            p3 = gp_Pnt(vertices[face[3]].X, vertices[face[3]].Y, vertices[face[3]].Z)
                            edge1 = BRepBuilderAPI_MakeEdge(p0, p2).Edge()
                            edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
                            edge3 = BRepBuilderAPI_MakeEdge(p3, p0).Edge()
                            wire = BRepBuilderAPI_MakeWire(edge1, edge2, edge3).Wire()
                            ocp_face = BRepBuilderAPI_MakeFace(wire).Face()
                            sewing.Add(ocp_face)
                            face_count += 1
                    except Exception as e:
                        logger.debug(f"FileConverter: Skipping face: {e}")
                        continue

                sewing.Perform()
                sewn_shape = sewing.SewedShape()
                builder.Add(compound, sewn_shape)

        if face_count == 0:
            raise ValueError("No convertible geometry found in 3DM file.")

        # Write STEP
        Interface_Static.SetCVal("write.step.schema", "AP214")
        writer = STEPControl_Writer()
        writer.Transfer(compound, STEPControl_AsIs)
        status = writer.Write(output_path)

        if status != 1:  # IFSelect_RetDone
            raise ValueError(f"STEP write failed with status {status}")

        logger.info(f"FileConverter: Successfully saved STEP to {output_path} ({face_count} faces)")
        return True
