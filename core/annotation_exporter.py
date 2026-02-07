"""
Annotation Exporter - Save and load annotations with 3D models.

Supports:
- JSON sidecar files for any format
- Image bundling for sharing
- Reader mode flag for view-only sharing
"""
import json
import logging
import os
import shutil
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class AnnotationExporter:
    """Handles exporting and importing annotations with 3D model files."""
    
    @staticmethod
    def get_annotation_file_path(model_path: str) -> str:
        """Get the path for the annotation sidecar JSON file.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            Path for the annotation JSON file (same name with .annotations.json)
        """
        base, _ = os.path.splitext(model_path)
        return f"{base}.annotations.json"
    
    @staticmethod
    def get_images_folder_path(model_path: str) -> str:
        """Get the path for the annotation images folder.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            Path for the annotation images folder
        """
        base, _ = os.path.splitext(model_path)
        return f"{base}_annotations"
    
    @staticmethod
    def save_annotations(annotations: List[dict], model_path: str, 
                        reader_mode: bool = False, bundle_images: bool = True) -> Tuple[bool, str]:
        """Save annotations to a sidecar JSON file.
        
        Args:
            annotations: List of annotation dictionaries from AnnotationPanel.export_annotations()
            model_path: Path to the 3D model file
            reader_mode: If True, marks annotations as read-only for recipients
            bundle_images: If True, copies images to a dedicated folder
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not annotations:
            return True, "No annotations to save"
        
        annotation_path = AnnotationExporter.get_annotation_file_path(model_path)
        images_folder = AnnotationExporter.get_images_folder_path(model_path)
        
        try:
            # Bundle images if requested and any annotations have images
            updated_annotations = []
            has_images = any(ann.get('image_paths') for ann in annotations)
            
            if bundle_images and has_images:
                # Create images folder
                if not os.path.exists(images_folder):
                    os.makedirs(images_folder)
                
                for ann in annotations:
                    ann_copy = ann.copy()
                    new_image_paths = []
                    
                    for i, img_path in enumerate(ann.get('image_paths', [])):
                        if os.path.exists(img_path):
                            # Get original extension
                            _, ext = os.path.splitext(img_path)
                            # Create new filename
                            new_filename = f"annotation_{ann['id']}_photo_{i+1}{ext}"
                            new_path = os.path.join(images_folder, new_filename)
                            
                            # Copy image
                            try:
                                shutil.copy2(img_path, new_path)
                                # Store relative path
                                folder_name = os.path.basename(images_folder)
                                new_image_paths.append(f"{folder_name}/{new_filename}")
                                logger.info(f"Copied image to {new_path}")
                            except Exception as e:
                                logger.warning(f"Failed to copy image {img_path}: {e}")
                                new_image_paths.append(img_path)  # Keep original path
                        else:
                            new_image_paths.append(img_path)
                    
                    ann_copy['image_paths'] = new_image_paths
                    updated_annotations.append(ann_copy)
            else:
                updated_annotations = annotations
            
            data = {
                'version': '1.0',
                'reader_mode': reader_mode,
                'model_file': os.path.basename(model_path),
                'annotations': updated_annotations,
            }
            
            with open(annotation_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(annotations)} annotations to {annotation_path}")
            return True, annotation_path
            
        except Exception as e:
            logger.error(f"Failed to save annotations: {e}", exc_info=True)
            return False, str(e)
    
    @staticmethod
    def load_annotations(model_path: str) -> Tuple[Optional[List[dict]], str, bool]:
        """Load annotations from a sidecar JSON file.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            tuple: (annotations: List[dict] or None, message: str, reader_mode: bool)
        """
        annotation_path = AnnotationExporter.get_annotation_file_path(model_path)
        
        if not os.path.exists(annotation_path):
            return None, "No annotation file found", False
        
        try:
            with open(annotation_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            annotations = data.get('annotations', [])
            reader_mode = data.get('reader_mode', False)
            
            # Resolve relative image paths
            model_dir = os.path.dirname(model_path)
            for ann in annotations:
                resolved_paths = []
                for img_path in ann.get('image_paths', []):
                    # Check if it's a relative path
                    if not os.path.isabs(img_path):
                        full_path = os.path.join(model_dir, img_path)
                        if os.path.exists(full_path):
                            resolved_paths.append(full_path)
                        else:
                            resolved_paths.append(img_path)
                    else:
                        resolved_paths.append(img_path)
                ann['image_paths'] = resolved_paths
            
            logger.info(f"Loaded {len(annotations)} annotations from {annotation_path} (reader_mode={reader_mode})")
            return annotations, f"Loaded {len(annotations)} annotations", reader_mode
            
        except Exception as e:
            logger.error(f"Failed to load annotations: {e}", exc_info=True)
            return None, str(e), False
    
    @staticmethod
    def export_with_model(mesh, annotations: List[dict], output_path: str, 
                         reader_mode: bool = True) -> Tuple[bool, str]:
        """Export a model with its annotations for sharing.
        
        Saves the mesh to the specified path and creates a sidecar .annotations.json file
        with reader_mode enabled for recipients.
        
        Args:
            mesh: PyVista mesh object
            annotations: List of annotation dictionaries
            output_path: Path for the output model file
            reader_mode: Mark as read-only for recipients (default True for sharing)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if mesh is None:
            return False, "No mesh provided"
        
        try:
            # Save the mesh
            mesh.save(output_path)
            logger.info(f"Saved mesh to {output_path}")
            
            # Save annotations if any
            if annotations:
                success, msg = AnnotationExporter.save_annotations(
                    annotations, output_path, 
                    reader_mode=reader_mode, 
                    bundle_images=True
                )
                if success:
                    logger.info(f"Saved annotations alongside mesh")
                    return True, f"Model and {len(annotations)} annotations saved"
                else:
                    logger.warning(f"Model saved but annotations failed: {msg}")
                    return True, f"Model saved, but annotations failed: {msg}"
            
            return True, "Model saved"
            
        except Exception as e:
            logger.error(f"Failed to export model: {e}", exc_info=True)
            return False, str(e)
    
    @staticmethod
    def annotations_exist(model_path: str) -> bool:
        """Check if annotations exist for a model file.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            True if annotation file exists
        """
        annotation_path = AnnotationExporter.get_annotation_file_path(model_path)
        return os.path.exists(annotation_path)
    
    @staticmethod
    def is_reader_mode(model_path: str) -> bool:
        """Check if the annotations for a model are in reader mode.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            True if reader_mode flag is set in the annotation file
        """
        annotation_path = AnnotationExporter.get_annotation_file_path(model_path)
        
        if not os.path.exists(annotation_path):
            return False
        
        try:
            with open(annotation_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('reader_mode', False)
        except Exception:
            return False
    
    @staticmethod
    def delete_annotations(model_path: str) -> Tuple[bool, str]:
        """Delete the annotation file and images folder for a model.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            tuple: (success: bool, message: str)
        """
        annotation_path = AnnotationExporter.get_annotation_file_path(model_path)
        images_folder = AnnotationExporter.get_images_folder_path(model_path)
        
        deleted = []
        
        try:
            if os.path.exists(annotation_path):
                os.remove(annotation_path)
                deleted.append("annotation file")
                logger.info(f"Deleted annotation file: {annotation_path}")
            
            if os.path.exists(images_folder):
                shutil.rmtree(images_folder)
                deleted.append("images folder")
                logger.info(f"Deleted images folder: {images_folder}")
            
            if not deleted:
                return True, "No annotation files to delete"
            
            return True, f"Deleted {', '.join(deleted)}"
            
        except Exception as e:
            logger.error(f"Failed to delete annotation files: {e}", exc_info=True)
            return False, str(e)
