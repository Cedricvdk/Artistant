using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

public sealed class BlenderFbxImporter : AssetPostprocessor
{
	private const string SourceFolder = "Assets/FBX/";
	private const string PrefabOutputFolder = "Assets/Prefabs/Auto";
	private const string ColliderSuffix = "_collider";

	// OnPostprocessModel fires before Unity persists sub-assets, so any mesh reference assigned
	// during that callback has no asset GUID and is serialized as null in the saved prefab.
	// OnPostprocessAllAssets fires after all sub-assets are fully written to disk, giving us
	// stable asset references that survive prefab serialization and source control round-trips.
	private static void OnPostprocessAllAssets(
		string[] importedAssets,
		string[] deletedAssets,
		string[] movedAssets,
		string[] movedFromAssetPaths)
	{
		foreach (string path in importedAssets)
		{
			if (ShouldProcess(path))
			{
				BuildOrUpdatePrefab(path);
			}
		}
	}

	private static void BuildOrUpdatePrefab(string fbxPath)
	{
		// Load mesh sub-assets directly from the persisted FBX asset.
		// These references have valid GUIDs and will survive prefab serialization.
		UnityEngine.Object[] subAssets = AssetDatabase.LoadAllAssetsAtPath(fbxPath);

		List<Mesh> colliderMeshes = new List<Mesh>();
		foreach (UnityEngine.Object asset in subAssets)
		{
			if (asset is Mesh mesh && IsColliderName(mesh.name))
			{
				colliderMeshes.Add(mesh);
			}
		}

		if (colliderMeshes.Count == 0)
		{
			Debug.LogWarning($"[BlenderFbxImporter] No collider meshes with suffix '{ColliderSuffix}' (optionally followed by digits) were found in '{fbxPath}'.");
		}

		GameObject fbxRoot = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
		if (fbxRoot == null)
		{
			Debug.LogWarning($"[BlenderFbxImporter] Could not load root GameObject from '{fbxPath}'.");
			return;
		}

		EnsureFolderExists(PrefabOutputFolder);

		string prefabName = Path.GetFileNameWithoutExtension(fbxPath);
		string prefabPath = $"{PrefabOutputFolder}/{prefabName}.prefab";

		// Instantiate a temporary copy — never mutate the source FBX asset directly.
		GameObject instance = UnityEngine.Object.Instantiate(fbxRoot);
		instance.name = prefabName;

		try
		{
			ApplyColliderRules(instance, colliderMeshes);
			PrefabUtility.SaveAsPrefabAsset(instance, prefabPath);
		}
		finally
		{
			UnityEngine.Object.DestroyImmediate(instance);
		}
	}

	private static bool ShouldProcess(string currentAssetPath)
	{
		if (string.IsNullOrEmpty(currentAssetPath))
		{
			return false;
		}

		if (!currentAssetPath.StartsWith(SourceFolder, StringComparison.OrdinalIgnoreCase))
		{
			return false;
		}

		return string.Equals(Path.GetExtension(currentAssetPath), ".fbx", StringComparison.OrdinalIgnoreCase);
	}

	private static void ApplyColliderRules(GameObject prefabRoot, List<Mesh> colliderMeshes)
	{
		// Collect nodes to destroy after all MeshColliders are assigned.
		// Destroying during iteration would invalidate GetComponentsInChildren results mid-loop.
		List<GameObject> nodesToDestroy = new List<GameObject>();

		foreach (Mesh colliderMesh in colliderMeshes)
		{
			Transform colliderTransform = FindTransformByName(prefabRoot.transform, colliderMesh.name);
			if (colliderTransform != null)
			{
				nodesToDestroy.Add(colliderTransform.gameObject);
			}

			// Add the MeshCollider to the prefab root with the real, persisted mesh asset reference.
			MeshCollider meshCollider = prefabRoot.AddComponent<MeshCollider>();
			meshCollider.sharedMesh = colliderMesh;
			meshCollider.convex = true;
		}

		// All colliders assigned — now safe to remove the source nodes from the hierarchy.
		foreach (GameObject node in nodesToDestroy)
		{
			UnityEngine.Object.DestroyImmediate(node);
		}
	}

	private static Transform FindTransformByName(Transform root, string targetName)
	{
		foreach (Transform child in root.GetComponentsInChildren<Transform>(true))
		{
			if (string.Equals(child.name, targetName, StringComparison.OrdinalIgnoreCase))
			{
				return child;
			}
		}

		return null;
	}

	private static bool IsColliderName(string name)
	{
		if (string.IsNullOrEmpty(name))
		{
			return false;
		}

		int suffixStart = name.LastIndexOf(ColliderSuffix, StringComparison.OrdinalIgnoreCase);
		if (suffixStart < 0)
		{
			return false;
		}

		int suffixEnd = suffixStart + ColliderSuffix.Length;
		for (int i = suffixEnd; i < name.Length; i++)
		{
			if (!char.IsDigit(name[i]))
			{
				return false;
			}
		}

		return true;
	}

	private static void EnsureFolderExists(string assetFolderPath)
	{
		string normalized = assetFolderPath.Replace('\\', '/').TrimEnd('/');
		string[] segments = normalized.Split('/');
		if (segments.Length < 2 || !string.Equals(segments[0], "Assets", StringComparison.Ordinal))
		{
			throw new ArgumentException($"Folder path must be under Assets/. Received: {assetFolderPath}");
		}

		string parent = segments[0];
		for (int i = 1; i < segments.Length; i++)
		{
			string child = segments[i];
			string currentPath = $"{parent}/{child}";
			if (!AssetDatabase.IsValidFolder(currentPath))
			{
				AssetDatabase.CreateFolder(parent, child);
			}

			parent = currentPath;
		}
	}
}
