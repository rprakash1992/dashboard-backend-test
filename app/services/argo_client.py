import os
import json
import httpx
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

ARGO_SERVER_URL = os.getenv("ARGO_SERVER_URL", "http://argo-server:2746")
ARGO_NAMESPACE = os.getenv("ARGO_NAMESPACE", "argo")
ARGO_TOKEN = os.getenv("ARGO_TOKEN", "")


@dataclass
class ArgoDeployment:
    """
    Represents an Argo WorkflowTemplate.
    `id` holds the template name, mirroring Prefect's deployment.id usage in callers.
    """

    id: str
    name: str


@dataclass
class ArgoWorkflowRun:
    """
    Represents a submitted Argo Workflow run.
    `id` holds the unique workflow run name (e.g. "extract-zip-abc12"),
    mirroring Prefect's FlowRun.id usage in callers.
    """

    id: str
    name: str


class ArgoClientService:
    def __init__(self):
        self.server_url = ARGO_SERVER_URL
        self.namespace = ARGO_NAMESPACE
        self.token = ARGO_TOKEN

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _submit_workflow(
        self,
        template_name: str,
        parameters: Dict[str, str],
    ) -> ArgoWorkflowRun:
        """Submit a workflow run from a WorkflowTemplate reference."""
        body = {
            "workflow": {
                "metadata": {
                    "generateName": f"{template_name}-",
                    "namespace": self.namespace,
                },
                "spec": {
                    "workflowTemplateRef": {"name": template_name},
                    "arguments": {
                        "parameters": [
                            {"name": k, "value": str(v)} for k, v in parameters.items()
                        ]
                    },
                },
            }
        }
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.server_url}/api/v1/workflows/{self.namespace}",
                json=body,
                headers=self._headers(),
                timeout=30.0,
            )
            if not response.is_success:
                print("argo submit error body>>>>", response.text)
            response.raise_for_status()
            data = response.json()
            print("submit workflow data>>", data)
        workflow_name = data["metadata"]["name"]
        workflow_id = data["metadata"]["uid"]
        return ArgoWorkflowRun(id=workflow_name, name=workflow_name)

    async def read_deployment_by_name(self, deployment_name: str) -> ArgoDeployment:
        """
        Fetch a WorkflowTemplate by name.

        `deployment_name` follows the Prefect convention "flow-name/deployment-name".
        The part before the slash is used as the Argo WorkflowTemplate name.
        Returns an ArgoDeployment whose `.id` is the template name, so callers
        can pass it directly to trigger_*_flow() without modification.
        """
        template_name = deployment_name.split("/")[0]
        # async with httpx.AsyncClient(verify=False) as client:
        #     response = await client.get(
        #         f"{self.server_url}/api/v1/workflow-templates/{self.namespace}/{template_name}",
        #         headers=self._headers(),
        #         timeout=30.0,
        #     )
        #     response.raise_for_status()

        return ArgoDeployment(id=template_name, name=template_name)

    async def trigger_extract_zip_flow(
        self,
        deployment_id: str,
        loggedin_user_id: str,
        selected_workspace_id: str,
        input_item_id: str,
        output_item_id: str,
    ) -> ArgoWorkflowRun:
        return await self._submit_workflow(
            template_name=deployment_id,
            parameters={
                "selected_workspace_id": selected_workspace_id,
                "loggedin_user_id": loggedin_user_id,
                "input_item_id": input_item_id,
                "output_item_id": output_item_id,
            },
        )

    async def trigger_compress_file_flow(
        self,
        deployment_id: str,
        selected_workspace_id: str,
        loggedin_user_id: str,
        input_item_id: str,
        output_item_id: str,
    ) -> ArgoWorkflowRun:
        return await self._submit_workflow(
            template_name=deployment_id,
            parameters={
                "selected_workspace_id": selected_workspace_id,
                "loggedin_user_id": loggedin_user_id,
                "input_item_id": input_item_id,
                "output_item_id": output_item_id,
            },
        )

    async def trigger_extract_zip_with_folder_structure_flow(
        self,
        deployment_id: str,
        selected_workspace_id: str,
        loggedin_user_id: str,
        input_item_id: str,
        output_item_id: str,
    ) -> ArgoWorkflowRun:
        return await self._submit_workflow(
            template_name=deployment_id,
            parameters={
                "selected_workspace_id": selected_workspace_id,
                "loggedin_user_id": loggedin_user_id,
                "input_item_id": input_item_id,
                "output_item_id": output_item_id,
            },
        )

    async def get_flow_run_status(self, flow_run_id: str) -> Dict[str, Any]:
        """
        Get the status of an Argo workflow run.
        `flow_run_id` is the workflow run name (e.g. "extract-zip-abc12").

        Argo phases: Pending | Running | Succeeded | Failed | Error
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{self.server_url}/api/v1/workflows/{self.namespace}/{flow_run_id}",
                headers=self._headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        status = data.get("status", {})
        phase = status.get("phase", "Pending")
        start_time_str = status.get("startedAt")
        end_time_str = status.get("finishedAt")

        return {
            "id": flow_run_id,
            "status": phase,
            "name": data["metadata"]["name"],
            "start_time": (
                datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                if start_time_str
                else None
            ),
            "end_time": (
                datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
                if end_time_str
                else None
            ),
        }

    async def get_flow_run(self, flow_run_id: str) -> Dict[str, Any]:
        """
        Get full details of an Argo workflow run.
        `flow_run_id` is the workflow run name (e.g. "extract-zip-abc12").

        Returns all available metadata, status, and per-step node details.
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{self.server_url}/api/v1/workflows/{self.namespace}/{flow_run_id}",
                headers=self._headers(),
                timeout=30.0,
            )
            print("response11", response)
            response.raise_for_status()
            data = response.json()
            print("data1", data)

        metadata = data.get("metadata", {})
        status = data.get("status", {})
        spec = data.get("spec", {})

        start_time_str = status.get("startedAt")
        end_time_str = status.get("finishedAt")

        nodes: Dict[str, Any] = {}
        for node_name, node in status.get("nodes", {}).items():
            node_start = node.get("startedAt")
            node_end = node.get("finishedAt")
            nodes[node_name] = {
                "id": node.get("id"),
                "name": node.get("name"),
                "display_name": node.get("displayName"),
                "type": node.get("type"),
                "phase": node.get("phase"),
                "message": node.get("message"),
                "start_time": (
                    datetime.fromisoformat(node_start.replace("Z", "+00:00"))
                    if node_start
                    else None
                ),
                "end_time": (
                    datetime.fromisoformat(node_end.replace("Z", "+00:00"))
                    if node_end
                    else None
                ),
            }

        return {
            "id": flow_run_id,
            "name": metadata.get("name"),
            "namespace": metadata.get("namespace"),
            "uid": metadata.get("uid"),
            "created_at": metadata.get("creationTimestamp"),
            "labels": metadata.get("labels", {}),
            "phase": status.get("phase", "Pending"),
            "message": status.get("message"),
            "start_time": (
                datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                if start_time_str
                else None
            ),
            "end_time": (
                datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
                if end_time_str
                else None
            ),
            "progress": status.get("progress"),
            "workflow_template": spec.get("workflowTemplateRef", {}).get("name"),
            "arguments": spec.get("arguments", {}).get("parameters", []),
            "nodes": nodes,
        }

    async def trigger_user_flow(
        self,
        s3_bucket: str,
        s3_folder: str,
        workflow_parameters: Dict[str, Any],
    ) -> ArgoWorkflowRun:
        """
        Submit a user-defined workflow stored in S3.
        `workflow_parameters` is serialized to JSON and passed as a single
        env var WORKFLOW_PARAMETERS. In workflow.py, read it with:
            import json, os
            params = json.loads(os.environ["WORKFLOW_PARAMETERS"])
        """
        return await self._submit_workflow(
            template_name="user-workflow",
            parameters={
                "s3_bucket": s3_bucket,
                "s3_folder": s3_folder,
                "workflow_parameters": json.dumps(workflow_parameters),
            },
        )

    async def trigger_flow_run_from_deployment_id(
        self,
        deployment_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> ArgoWorkflowRun:
        print("triggering deployment>>>>>>>")
        return await self._submit_workflow(
            template_name=deployment_id,
            parameters=parameters or {},
        )
