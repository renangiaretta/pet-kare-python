from rest_framework.views import APIView, Request, Response, status
from .models import Pet
from .serializers import PetSerializer
from groups.models import Group
from traits.models import Trait
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        pets = Pet.objects.all()
        query_params = request.query_params.get('trait', None)
        if query_params:
            pets = pets.filter(traits__name__iexact=query_params)
        result_page = self.paginate_queryset(pets, request, view=self)
        serializer = PetSerializer(result_page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group_dict = serializer.validated_data.pop('group')
        traits = serializer.validated_data.pop('traits')
        pet_obj = Pet.objects.create(**serializer.validated_data)
        group = Group.objects.get_or_create(scientific_name=group_dict['scientific_name'])
        pet_obj.group = group[0]
        for trait in traits:
            trait_obj = Trait.objects.filter(name__iexact=trait['name']).first()
            if not trait_obj:
                trait_obj = Trait.objects.create(**trait)
            pet_obj.traits.add(trait_obj)
        pet_obj.save()
        serializer = PetSerializer(pet_obj)
        return Response(serializer.data, status.HTTP_201_CREATED)


class PetDetailView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(pet)
        return Response(serializer.data, status.HTTP_200_OK)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        group_dict = serializer.validated_data.pop('group', None)
        traits = serializer.validated_data.pop('traits', [])
        if group_dict:
            group, _ = Group.objects.update_or_create(
                scientific_name__iexact=group_dict['scientific_name'],
                defaults=group_dict,
            )
            pet.group = group
        pet.save()

        for trait in traits:
            trait_obj = Trait.objects.filter(name__iexact=trait['name']).first()
            if not trait_obj:
                trait_obj = Trait.objects.create(**trait)
            pet.traits.add(trait_obj)
        pet.save()
        if serializer.validated_data:
            pet = serializer.update(pet, serializer.validated_data)
        serializer = PetSerializer(pet)
        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        pet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
