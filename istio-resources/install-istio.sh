#!/usr/bin/env bash
export ISTIO_VERSION=1.7.7
rm -rf istio-${ISTIO_VERSION}
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
cd istio-${ISTIO_VERSION}/bin

#1.6 install steps were different
if  [[ $ISTIO_VERSION == 1.6* ]] ;
then

   echo 'Installing istio'
   ./istioctl manifest apply --set profile=default
   cat << EOF > ./local-cluster-gateway.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  profile: empty
  components:
    ingressGateways:
      - name: cluster-local-gateway
        enabled: true
        label:
          istio: cluster-local-gateway
          app: cluster-local-gateway
        k8s:
          service:
            type: ClusterIP
            ports:
            - port: 15020
              name: status-port
            - port: 80
              name: http2
            - port: 443
              name: https
  values:
    gateways:
      istio-ingressgateway:
        debug: error
EOF

   ./istioctl manifest generate -f local-cluster-gateway.yaml > manifest.yaml
   kubectl apply -f manifest.yaml
   echo 'istio & gateway setup completed'


else

#1.7 (and hopefully above) steps
   echo 'Installing istio'
   cat << EOF > ./local-cluster-gateway.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    accessLogFile: /dev/stdout
  values:
    security:
      selfSigned: false
    global:
      controlPlaneSecurityEnabled: true
      proxy:
        autoInject: disabled
        excludeInboundPorts: "9090"
        excludeOutboundPorts: "15021"
      useMCP: false
      mtls:
        enabled: true
      meshExpansion:
        enabled: true
  addonComponents:
    pilot:
      enabled: true
    prometheus:
      enabled: true
    kiali:
      enabled: true
  components:
    ingressGateways:
      - name: cluster-local-gateway
        enabled: true
        label:
          istio: cluster-local-gateway
          app: cluster-local-gateway
        k8s:
          service:
            type: ClusterIP
            ports:
            - port: 15020
              name: status-port
            - port: 80
              targetPort: 8080
              name: http2
            - port: 443
              targetPort: 8443
              name: https
      - name: istio-ingressgateway
        enabled: true
        k8s:
          hpaSpec:
            maxReplicas: 5
            metrics:
              - resource:
                  name: cpu
                  targetAverageUtilization: 80
                type: Resource
            minReplicas: 1
            scaleTargetRef:
              apiVersion: apps/v1
              kind: Deployment
              name: istio-ingressgateway
          resources:
            limits:
              cpu: 2000m
              memory: 1024Mi
            requests:
              cpu: 100m
              memory: 128Mi
          strategy:
            rollingUpdate:
              maxSurge: 100%
              maxUnavailable: 25%
      - name: istio-ops-ingressgateway
        enabled: true
        k8s:
          hpaSpec:
            maxReplicas: 5
            metrics:
              - resource:
                  name: cpu
                  targetAverageUtilization: 80
                type: Resource
            minReplicas: 1
            scaleTargetRef:
              apiVersion: apps/v1
              kind: Deployment
              name: istio-ops-ingressgateway
          resources:
            limits:
              cpu: 2000m
              memory: 1024Mi
            requests:
              cpu: 100m
              memory: 128Mi
          strategy:
            rollingUpdate:
              maxSurge: 100%
              maxUnavailable: 25%
          overlays:
            - kind: HorizontalPodAutoscaler
              name: istio-ops-ingressgateway
              patches:
                - path: metadata.labels.app
                  value: istio-ops-ingressgateway
                - path: metadata.labels.istio
                  value: ops-ingressgateway
                - path: spec.scaleTargetRef.name
                  value: istio-ops-ingressgateway
            - kind: Deployment
              name: istio-ops-ingressgateway
              patches:
                - path: metadata.labels.app
                  value: istio-ops-ingressgateway
                - path: metadata.labels.istio
                  value: ops-ingressgateway
                - path: spec.selector.matchLabels.app
                  value: istio-ops-ingressgateway
                - path: spec.selector.matchLabels.istio
                  value: ops-ingressgateway
                - path: spec.template.metadata.labels.app
                  value: istio-ops-ingressgateway
                - path: spec.template.metadata.labels.istio
                  value: ops-ingressgateway
            - kind: Service
              name: istio-ops-ingressgateway
              patches:
                - path: metadata.labels.app
                  value: istio-ops-ingressgateway
                - path: metadata.labels.istio
                  value: ops-ingressgateway
                - path: spec.selector.app
                  value: istio-ops-ingressgateway
                - path: spec.selector.istio
                  value: ops-ingressgateway
  values:
    gateways:
      istio-ingressgateway:
        debug: error
EOF

   ./istioctl install -f local-cluster-gateway.yaml
   echo 'istio & gateway setup completed'

fi